import os
import json
import logging
import shutil
import re
import ast
import asyncio
import time
from pathlib import PurePosixPath
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor
try:
    from langchain_openai import ChatOpenAI
except ModuleNotFoundError:
    # Permet aux tests allégés d'importer agents.dev sans dépendance OpenAI installée.
    class ChatOpenAI:  # type: ignore[override]
        def __init__(self, *args, **kwargs):
            self._args = args
            self._kwargs = kwargs

        def get_num_tokens(self, text: str) -> int:
            return max(1, len(text) // 4)

        def bind_tools(self, *args, **kwargs):
            raise ModuleNotFoundError("langchain_openai is required to execute dev_agent()")

        def invoke(self, *args, **kwargs):
            raise ModuleNotFoundError("langchain_openai is required to execute dev_agent()")
try:
    from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
except ModuleNotFoundError:
    class _BaseMessage:
        def __init__(self, content="", tool_calls=None, tool_call_id=None):
            self.content = content
            self.tool_calls = tool_calls or []
            self.tool_call_id = tool_call_id

    class HumanMessage(_BaseMessage):
        pass

    class SystemMessage(_BaseMessage):
        pass

    class ToolMessage(_BaseMessage):
        pass

# Import des shared tools
from .shared_tools import (
    write_file,
    validate_syntax,
    prisma_migrate,
    rag_search,
    read_files,
    run_build,
    get_stack_id,
    _write_learner_event,
    run_tsc_check,        # Phase 2 — check déterministe per-file
    run_eslint_check,     # Phase 2 — check déterministe ESLint per-file
    run_prisma_validate,  # Phase 2 — gate pré-build prisma
)
try:
    from .llm_runner import LLMConversationRunner
except ModuleNotFoundError:
    class LLMConversationRunner:  # type: ignore[override]
        def __init__(self, llm, messages: list) -> None:
            self.llm = llm
            self.messages = messages

        def inject(self, content: str) -> None:
            self.messages.append(HumanMessage(content=content))

        def _compact(self, text: str) -> str:
            return re.sub(r"\s+", " ", text).strip()

        def _shrink_tool_output(self, tool_name: str, output: str, max_chars: int = 1800) -> str:
            compact = self._compact(output)
            if len(compact) <= max_chars:
                return compact
            head = max_chars // 2
            tail = max_chars - head
            return (
                f"[{tool_name}] OUTPUT_TRUNCATED total_chars={len(compact)} | "
                f"head: {compact[:head]} ... tail: {compact[-tail:]}"
            )

        def _main_context(self, messages_list: list, max_chars: int = 14000) -> list:
            if len(messages_list) <= 2:
                return messages_list
            kept = [messages_list[0], messages_list[1]]
            turns = []
            i = 2
            n = len(messages_list)
            while i < n:
                msg = messages_list[i]
                has_tool_calls = hasattr(msg, "tool_calls") and bool(getattr(msg, "tool_calls", None))
                if has_tool_calls:
                    turn = [msg]
                    i += 1
                    while i < n and isinstance(messages_list[i], ToolMessage):
                        turn.append(messages_list[i])
                        i += 1
                    expected_ids = {tc.get("id") for tc in msg.tool_calls if tc.get("id")}
                    got_ids = {tm.tool_call_id for tm in turn[1:] if getattr(tm, "tool_call_id", None)}
                    if expected_ids and expected_ids.issubset(got_ids):
                        turns.append(turn)
                else:
                    if isinstance(msg, ToolMessage):
                        i += 1
                        continue
                    turns.append([msg])
                    i += 1
            if not turns:
                return kept
            last_turn = turns[-1]
            turn_chars = sum(len(str(getattr(m, "content", ""))) for m in last_turn)
            if turn_chars > max_chars:
                for msg in reversed(messages_list[2:]):
                    if not isinstance(msg, ToolMessage):
                        return kept + [msg]
                return kept
            return kept + last_turn
from .stack_config import (
    get_blueprint,
    get_root_file,
    get_cleanup_artifacts,
    get_workdir_keep_extra,
    get_forbidden_paths,
    get_forbidden_imports,
)
from utils.prompt_loader import load_stack_prompt
try:
    from .conformity_agent import run_conformity_supervisor
except ModuleNotFoundError:
    async def run_conformity_supervisor(*args, **kwargs):  # type: ignore[override]
        return {"status": "skipped", "confidence": 0.0}

try:
    from .security_agent import run_security_supervisor
except ModuleNotFoundError:
    async def run_security_supervisor(*args, **kwargs):  # type: ignore[override]
        return {"status": "skipped", "confidence": 0.0}

try:
    from .architecture_agent import run_architecture_supervisor
except ModuleNotFoundError:
    async def run_architecture_supervisor(*args, **kwargs):  # type: ignore[override]
        return {"status": "skipped", "confidence": 0.0}

try:
    from .build_supervisor_agent import run_build_supervisor
except ModuleNotFoundError:
    async def run_build_supervisor(*args, **kwargs):  # type: ignore[override]
        return {"status": "skipped"}
from .requirements_engine import (
    gate_check as _engine_gate_check,
    compute_coverage_detailed as _engine_compute_coverage_detailed,
)
from .file_supervision_loop import FileSupervisionLoop
from .dev_path_utils import (
    make_priority_ranker,
    sort_paths_by_priority,
    resolve_max_iterations,
    extract_primary_path_from_requirement,
    sort_requirements_by_priority,
    allowed_paths_for_blocker,
    path_is_allowed_for_objective,
    find_project_dir,
    first_directive_line,
    collect_forbidden_import_violations as _collect_forbidden_import_violations,  # backward compat
)
from .pre_build_validator import PreBuildValidator
from .dev_reflection import ProgressSummary, build_iteration_brief
from .supervision_manager import run_pre_build_deterministic_checks
from .build_state_manager import BuildStateManager

# Logger
logger = logging.getLogger(__name__)
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")


def _avg(values: list[float]) -> float:
    if not values:
        return 0.0
    return round(sum(values) / len(values), 3)


def _match_supervision_routing_inline(
    file_path: str,
    routing: dict[str, list[str]],
) -> list[str]:
    """
    Match glob supervision routing sans dépendre de dev_test_agent
    (évite une boucle d'import dev.py <-> dev_test_agent.py).
    """
    from fnmatch import fnmatch

    norm = (file_path or "").replace("\\", "/")
    for pattern, supervisors in (routing or {}).items():
        if fnmatch(norm, pattern):
            return supervisors or []
    return []


async def _supervise_file_inline(
    file_path: str,
    file_content: str,
    context: dict,
    supervisors: list[str],
    conformity_scores: list,
    security_scores: list,
    architecture_scores: list,
    timeout_ms: int = 30000,
    project_dir: str = "",
) -> tuple[str | None, dict]:
    """
    Niveau 1 — Checks déterministes (tsc, prisma validate) : faits, pas opinions.
    Niveau 2 — Superviseurs LLM sémantiques : contexte enrichi avec résultat outils.
    Retourne (message_correction, résultats_normalisés).
    """
    # ── Niveau 1 : Checks déterministes ──────────────────────────────────────
    norm_path = (file_path or "").replace("\\", "/")
    is_ts_file = norm_path.endswith(".ts") or norm_path.endswith(".tsx")
    is_prisma_schema = norm_path == "prisma/schema.prisma"
    det_errors: list[str] = []
    det_context_str = ""

    if project_dir:
        if is_ts_file:
            tsc_result: dict = {"errors": [], "success": True, "skipped": True}
            eslint_result: dict = {"errors": [], "success": True, "skipped": True}
            try:
                tsc_result, eslint_result = await asyncio.gather(
                    run_tsc_check(project_dir),
                    run_eslint_check(project_dir),
                )
            except Exception as _det_exc:
                logger.debug(f"[det_check] checks TS/ESLint non-bloquants sur {norm_path}: {_det_exc}")

            # Filtrer TSC sur le fichier courant
            tsc_file_errors: list[dict] = []
            try:
                if not tsc_result.get("skipped"):
                    tsc_file_errors = [
                        e for e in tsc_result.get("errors", [])
                        if norm_path in (e.get("file", "") or "").replace("\\", "/")
                    ]
            except Exception as _tsc_exc:
                logger.debug(f"[det_check] tsc non-bloquant sur {norm_path}: {_tsc_exc}")

            # Filtrer ESLint sur le fichier courant
            eslint_file_errors: list[dict] = []
            try:
                if not eslint_result.get("skipped"):
                    eslint_file_errors = [
                        e for e in eslint_result.get("errors", [])
                        if norm_path in (e.get("file", "") or "").replace("\\", "/")
                    ]
            except Exception as _eslint_exc:
                logger.debug(f"[det_check] eslint non-bloquant sur {norm_path}: {_eslint_exc}")

            if tsc_file_errors:
                for err in tsc_file_errors[:5]:
                    det_errors.append(
                        f"  [tsc] L{err.get('line', '')}:{err.get('col', '')} "
                        f"{err.get('code', '')} — {err.get('message', '')}"
                    )
            if eslint_file_errors:
                for err in eslint_file_errors[:5]:
                    det_errors.append(
                        f"  [eslint] L{err.get('line', '')}:{err.get('col', '')} "
                        f"{err.get('code', '')} — {err.get('message', '')}"
                    )

            if tsc_file_errors or eslint_file_errors:
                det_context_str = (
                    f"[tsc] {len(tsc_file_errors)} erreur(s), "
                    f"[eslint] {len(eslint_file_errors)} erreur(s)"
                )
            else:
                det_context_str = "[tsc+eslint] pas d'erreur"
        elif is_prisma_schema:
            # prisma validate --schema est incompatible avec Prisma 7.5.0 (url dans prisma.config.ts,
            # pas dans le schema). La validation réelle se fait à npm run build → prisma generate.
            det_context_str = "[prisma validate] skipped (Prisma 7.5 — url in prisma.config.ts)"

    if det_errors:
        tool_name = "tsc/eslint" if is_ts_file else "prisma validate"
        logger.info(
            f"[det_check] {norm_path} — {len(det_errors)} erreur(s) {tool_name} → correction sans LLM"
        )
        return (
            f"ERREUR {tool_name.upper()} sur {file_path} :\n"
            + "\n".join(det_errors)
            + f"\nCorrige ces erreurs dans {file_path} avec write_file() maintenant.",
            {"deterministic": {"status": "needs_fix", "confidence": 1.0, "tool": tool_name}},
        )

    # ── Niveau 2 : Superviseurs LLM ──────────────────────────────────────────
    # Contexte enrichi avec résultat déterministe si disponible
    if det_context_str:
        context = {**context, "det_tool_result": det_context_str}

    tasks = {}
    _det = context.get("det_tool_result", "")
    if "conformity" in supervisors:
        tasks["conformity"] = run_conformity_supervisor(
            file_path=file_path,
            file_content=file_content,
            requirements=context.get("requirements", []),
            plan=context.get("plan", {}),
            files_so_far=context.get("files_so_far", {}),
            project_name=context.get("project_name", ""),
            run_id=context.get("run_id", ""),
            stack_id=context.get("stack_id", "nextjs-clerk-prisma"),
            det_tool_result=_det,
        )
    if "security" in supervisors:
        tasks["security"] = run_security_supervisor(
            file_path=file_path,
            file_content=file_content,
            prisma_schema=context.get("prisma_schema", ""),
            project_name=context.get("project_name", ""),
            run_id=context.get("run_id", ""),
            stack_id=context.get("stack_id", "nextjs-clerk-prisma"),
            det_tool_result=_det,
        )
    if "architecture" in supervisors:
        tasks["architecture"] = run_architecture_supervisor(
            file_path=file_path,
            file_content=file_content,
            prisma_schema=context.get("prisma_schema", ""),
            plan=context.get("plan", {}),
            files_so_far=context.get("files_so_far", {}),
            project_name=context.get("project_name", ""),
            run_id=context.get("run_id", ""),
            stack_id=context.get("stack_id", "nextjs-clerk-prisma"),
            det_tool_result=_det,
        )

    timeout_s = max(0.001, float(timeout_ms) / 1000.0)

    async def _run_one(name: str, coro):
        try:
            result = await asyncio.wait_for(coro, timeout=timeout_s)
            return name, result
        except asyncio.TimeoutError:
            return name, {"status": "skipped", "confidence": 0.0, "note": "timeout"}
        except Exception:
            return name, {"status": "skipped", "confidence": 0.0}

    corrections: list[str] = []
    results: dict = {}
    gathered = await asyncio.gather(
        *[_run_one(name, coro) for name, coro in tasks.items()],
        return_exceptions=False,
    )
    for name, result in gathered:
        results[name] = result
        conf = float(result.get("confidence", 0.0) or 0.0)
        if name == "conformity":
            conformity_scores.append(conf)
        elif name == "security":
            security_scores.append(conf)
        elif name == "architecture":
            architecture_scores.append(conf)

        status = str(result.get("status", "") or "").lower()
        if status == "needs_fix" and conf > 0.7:
            fix = result.get("fix_instruction", {}) or {}
            if fix.get("problem") and fix.get("fix"):
                corrections.append(
                    f"[SUPERVISEUR {name.upper()}] {fix['problem']}\n"
                    f"Fix obligatoire : {fix['fix']}"
                )

    if corrections:
        return (
            f"CORRECTIONS SUPERVISEURS OBLIGATOIRES sur {file_path} :\n"
            + "\n\n".join(corrections)
            + "\nApplique ces corrections avec write_file() maintenant.",
            results,
        )
    return None, results


async def _run_build_supervisor_inline(
    build_stderr: str,
    files: dict,
    run_id: str,
    stack_id: str,
) -> str | None:
    result = await run_build_supervisor(
        build_stderr=build_stderr,
        combined_files=files,
        run_id=run_id or "",
        stack_id=stack_id or "nextjs-clerk-prisma",
    )
    if str(result.get("status", "")).lower() == "needs_fix":
        fix = result.get("fix_instruction", {}) or {}
        if fix.get("problem") and fix.get("fix"):
            return (
                f"[BUILD SUPERVISOR] Erreur identifiée dans {fix.get('file', '?')}:\n"
                f"{fix['problem']}\n"
                f"Fix minimal : {fix['fix']}\n"
                "Applique ce fix avec write_file() puis rappelle run_build()."
            )
    return None



# Répertoires système à préserver lors du nettoyage inter-runs (invariants multi-stack)
_WORKDIR_KEEP_SYSTEM = {"logs", "config", "snapshots", "__pycache__", ".git"}


def _clean_project_workdir(workdir: str, extra_keep: set[str] | None = None) -> None:
    """
    Supprime les fichiers source du run précédent dans FACTORY_WORKDIR.

    Problème : le cleanup de fin de run ne supprime que node_modules/.next/__pycache__.
    Les fichiers source (package.json, app/, middleware.ts…) restent sur disque.
    Au run suivant, le LLM appelle read_files, voit ces fichiers, conclut que le
    projet est déjà généré et ne produit que jest.setup.js → SEMANTIC_VIOLATION.

    Solution : supprimer tous les fichiers/dossiers non-système en début de run.
    extra_keep : répertoires stack-spécifiques à préserver (ex: node_modules pour Node.js).
    """
    keep = _WORKDIR_KEEP_SYSTEM | (extra_keep or set())
    if not workdir or not os.path.isdir(workdir):
        return
    try:
        for item in os.listdir(workdir):
            if item in keep:
                continue
            full = os.path.join(workdir, item)
            try:
                if os.path.isfile(full) or os.path.islink(full):
                    os.remove(full)
                    logger.info(f"[pre-run cleanup] Fichier supprimé : {item}")
                elif os.path.isdir(full):
                    shutil.rmtree(full, ignore_errors=True)
                    logger.info(f"[pre-run cleanup] Répertoire supprimé : {item}")
            except Exception as item_err:
                logger.warning(f"[pre-run cleanup] Impossible de supprimer {item}: {item_err}")
    except Exception as e:
        logger.warning(f"[pre-run cleanup] Erreur listage workdir '{workdir}': {e}")


def _write_template_files(workdir: str, stack_cfg: dict, project_name: str, stack_id: str) -> dict:
    """
    Écrit les fichiers templates sur disque AVANT la boucle LLM.
    Ces fichiers sont invariants pour la stack — le LLM ne doit pas les régénérer.
    Retourne {nom_fichier: contenu} des fichiers écrits.
    """
    import pathlib
    templated = stack_cfg.get("templated_files", {})
    if not templated or not workdir:
        return {}

    # Répertoire base : factory-sprint0/config/stacks/{stack_id}/
    base_dir = pathlib.Path(__file__).parent.parent / "config" / "stacks" / stack_id

    written = {}
    for dest_filename, template_rel_path in templated.items():
        try:
            template_path = base_dir / template_rel_path
            if not template_path.exists():
                logger.warning(f"[templates] Template introuvable: {template_path}")
                continue
            content = template_path.read_text(encoding="utf-8")
            content = content.replace("{project_name}", project_name)
            dest_path = pathlib.Path(workdir) / dest_filename
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            dest_path.write_text(content, encoding="utf-8")
            written[dest_filename] = content
            logger.info(f"[templates] ✓ {dest_filename} écrit depuis template")
        except Exception as e:
            logger.warning(f"[templates] Erreur écriture {dest_filename}: {e}")
    return written


# --- Dev Agent v3 Ultimate – Version 3.2 Breakthrough (Premier SaaS imminent) ---
def dev_agent(
    spec: str,
    mermaid: str,
    project_name: str = "default-project",
    run_id: str = "",
    stack_id: str = "",
    requirements: list = None,
    spec_unmatched: list = None,
    plan: dict = None,
) -> dict:
    """
    Dev Agent v3 Ultimate – Version finale stable.
    Correction boucle jest.config.js + détection run_build + progression forcée.
    """
    # Nettoyage du workdir avant toute génération — évite la contamination inter-runs.
    _workdir = os.getenv("FACTORY_WORKDIR", "")
    _extra_keep = set(get_workdir_keep_extra(stack_id)) if stack_id else set()
    if _workdir:
        _clean_project_workdir(_workdir, extra_keep=_extra_keep)

    # max_retries=3 couvre les 429 transitoires avec backoff LangChain.
    # with_fallbacks non applicable ici : bind_tools n'est pas disponible
    # sur RunnableWithFallbacks — fallback model pour dev différé (T007.5).
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, max_retries=3)

    # Tous les outils disponibles dès l'itération 1 — le Blueprint Validator bloque
    # run_build si des fichiers obligatoires manquent (gate suffisant).
    # Supprimer le split Phase1/Phase2 qui causait 55% des runs à atteindre MAX_ITERATIONS.
    tools_phase1 = [write_file, validate_syntax, prisma_migrate, rag_search, read_files, run_build]
    tools_phase2 = tools_phase1
    tool_map = {tool.name: tool for tool in tools_phase1}

    DEFAULT_MAX_ITERATIONS = 14
    MAX_ITERATIONS = DEFAULT_MAX_ITERATIONS
    MAX_BUILD_ATTEMPTS = 8
    PHASE1_LIMIT = MAX_ITERATIONS  # aligné dynamiquement après chargement stack
    # Budgets ramenés à des tailles réalistes pour limiter la pression TPM
    MAX_SPEC_TOKENS = 4000
    MAX_MERMAID_TOKENS = 1200
    MAX_TOOL_OUTPUT_CHARS = 1800
    MAX_MAIN_HISTORY_CHARS = 14000

    def summarize_text(text: str, max_tokens: int, description: str) -> str:
        try:
            current_tokens = llm.get_num_tokens(text)
        except Exception:
            current_tokens = len(text) // 4
        if current_tokens <= max_tokens:
            return text
        try:
            summary = llm.invoke([
                SystemMessage(content=f"Résume en moins de {max_tokens} tokens pour le développement."),
                HumanMessage(content=text)
            ]).content
            return summary
        except Exception:
            return text[:int(max_tokens * 3.5)] + "\n\n[TRUNCATED]"

    summarized_spec = summarize_text(spec, MAX_SPEC_TOKENS, "Specification")
    summarized_mermaid = summarize_text(mermaid, MAX_MERMAID_TOKENS, "Mermaid Diagram")

    effective_stack_id = stack_id or get_stack_id()
    prompt = load_stack_prompt("dev", effective_stack_id)
    from .stack_config import load_stack_config
    stack_cfg = load_stack_config(effective_stack_id) or {}
    try:
        _supervision_routing = load_stack_config(
            stack_id or "nextjs-clerk-prisma"
        ).get("supervision_routing", {})
    except Exception:
        _supervision_routing = {}
    _supervision_cfg = stack_cfg.get("supervision", {}) if isinstance(stack_cfg, dict) else {}
    try:
        _supervision_batch_size = int(_supervision_cfg.get("batch_size", 3))
    except Exception:
        _supervision_batch_size = 3
    if _supervision_batch_size < 1:
        _supervision_batch_size = 1
    try:
        _supervisor_timeout_ms = int(_supervision_cfg.get("supervisor_timeout_ms", 30000))
    except Exception:
        _supervisor_timeout_ms = 30000
    if _supervisor_timeout_ms < 1:
        _supervisor_timeout_ms = 30000

    generation_order_cfg = stack_cfg.get("generation_order", {}) if isinstance(stack_cfg, dict) else {}
    _priority_paths_cfg = generation_order_cfg.get("priority_paths", []) if isinstance(generation_order_cfg, dict) else []
    _path_priority_ranker = make_priority_ranker(_priority_paths_cfg)

    MAX_ITERATIONS = resolve_max_iterations(stack_cfg, requirements, default=DEFAULT_MAX_ITERATIONS)
    PHASE1_LIMIT = MAX_ITERATIONS
    logger.info(
        f"[ITERATION_POLICY] requirements={len(requirements or [])} "
        f"max_iterations={MAX_ITERATIONS}"
    )

    # ── Écriture des fichiers templates AVANT la boucle LLM ──────────────────
    # Ces fichiers sont invariants pour la stack. Le LLM ne doit pas les régénérer.
    _template_written = _write_template_files(_workdir, stack_cfg, project_name, effective_stack_id)
    _templated_names = set(_template_written.keys())

    blueprint = get_blueprint(effective_stack_id)
    required_files = blueprint.get("required_files", []) if isinstance(blueprint, dict) else []
    mandatory_rag_queries = stack_cfg.get("mandatory_rag_queries", [])
    try:
        mandatory_rag_k = int(stack_cfg.get("mandatory_rag_k", 4))
    except Exception:
        mandatory_rag_k = 4
    try:
        mandatory_rag_snippet_chars = int(stack_cfg.get("mandatory_rag_snippet_chars", 900))
    except Exception:
        mandatory_rag_snippet_chars = 900
    mandatory_rag_context_chunks = []
    for query in mandatory_rag_queries:
        try:
            rag_result = rag_search.invoke({"query": query, "k": mandatory_rag_k})
            mandatory_rag_context_chunks.append(
                f"[RAG::{query}]\n{str(rag_result)[:mandatory_rag_snippet_chars]}"
            )
        except Exception as rag_err:
            mandatory_rag_context_chunks.append(f"[RAG::{query}] ERROR: {rag_err}")
    mandatory_rag_context = "\n\n".join(mandatory_rag_context_chunks)

    # scaffold_extends : fichiers pré-écrits par template mais étendus par le LLM (ex: prisma/schema.prisma).
    # Ils sont exemptés du bloc "NE PAS RÉÉCRIRE" et restent dans llm_required_files.
    scaffold_extends_cfg = stack_cfg.get("scaffold_extends", {})
    scaffold_extends_paths = set(scaffold_extends_cfg.keys())

    # Exclure les fichiers templates de l'ordre de génération LLM (sauf scaffold_extends)
    _templated_protected = _templated_names - scaffold_extends_paths
    llm_required_files = sort_paths_by_priority([f for f in required_files if f not in _templated_protected], _path_priority_ranker)
    templates_block = ""
    if _templated_protected:
        templates_block = (
            "FICHIERS DÉJÀ ÉCRITS PAR LA FACTORY (templates validés — NE PAS RÉÉCRIRE) :\n"
            + "\n".join(f"  ✓ {f}" for f in sorted(_templated_protected))
            + "\nCes fichiers sont corrects sur le disque. Concentre-toi sur les fichiers MÉTIER ci-dessous.\n\n"
        )
    # required_files_block : tous les fichiers obligatoires.
    # Pour les scaffold_extends, note courte sans mention "pré-écrit" (évite la paralysie).
    required_files_block = ""
    if llm_required_files:
        lines = []
        for i, f in enumerate(llm_required_files):
            if f in scaffold_extends_paths:
                kw = scaffold_extends_cfg[f].get("locked_until_keyword", "model ").strip()
                lines.append(f"{i+1}. {f}  ← écrire les blocs `{kw} NomDuModele {{...}}` du brief")
            else:
                lines.append(f"{i+1}. {f}")
        required_files_block = (
            "FICHIERS OBLIGATOIRES À CRÉER (en plus des fichiers métier de la spec) :\n"
            + "\n".join(lines)
            + "\n\n"
        )
    scaffold_schema_block = ""  # plus utilisé — logique fusionnée dans required_files_block
    requirements_block = ""
    if requirements:
        reqs_list = "\n".join(f"  - {r}" for r in requirements)
        requirements_block = (
            "FONCTIONNALITÉS OBLIGATOIRES — chaque item DOIT être implémenté dans les fichiers générés :\n"
            f"{reqs_list}\n"
            "⚠️ Tu ne peux pas déclarer le run terminé avant d'avoir créé UN fichier par page et par route API listée ci-dessus. "
            "Vérifie cette liste avant chaque appel à run_build.\n\n"
        )
    spec_degraded_block = ""
    if spec_unmatched:
        unmatched_list = "\n".join(f"  - {r}" for r in spec_unmatched)
        spec_degraded_block = (
            "⚠️ NOMS CANONIQUES OBLIGATOIRES — PRIORITÉ ABSOLUE SUR LA SPEC\n"
            "La spec a été générée avec des noms qui diffèrent des requirements du client.\n"
            "Pour les éléments ci-dessous, IGNORER les noms de la spec et utiliser EXACTEMENT ceux des requirements :\n"
            f"{unmatched_list}\n"
            "Règle absolue : si la spec nomme un modèle '<NomDansSpec>', le client exige '<NomDansRequirements>'. "
            "Si la spec utilise '/<cheminSpec>', le client exige '/<cheminRequirements>'. "
            "Tu dois implémenter les noms des requirements MOT POUR MOT — pas leurs équivalents dans la spec.\n\n"
        )
    packages = stack_cfg.get("packages", {})
    packages_block = ""
    if packages:
        packages_block = (
            "VERSIONS DE PACKAGES OBLIGATOIRES (copier exactement dans package.json, ne pas modifier) :\n"
            + "\n".join(f'  "{pkg}": "{ver}"' for pkg, ver in packages.items())
            + "\n\n"
        )
    dev_packages = stack_cfg.get("dev_packages", {})
    dev_packages_block = ""
    if dev_packages:
        dev_packages_block = (
            "DEV DEPENDENCIES OBLIGATOIRES (copier exactement dans devDependencies) :\n"
            + "\n".join(f'  "{pkg}": "{ver}"' for pkg, ver in dev_packages.items())
            + "\n\n"
        )
    # Bloc d'ordre adaptatif — basé sur llm_required_files (fichiers réellement à écrire par le LLM,
    # templates déjà exclus). Si package.json apparaît (templates non fonctionnels), il est
    # remonté en tête quelle que soit la priorité generation_order.
    # ordering_block : tous les fichiers obligatoires dans l'ordre de priorité.
    ordering_block = ""
    if llm_required_files:
        _ordered = list(llm_required_files)
        if "package.json" in _ordered:
            _ordered.remove("package.json")
            _ordered.insert(0, "package.json")
        ordering_block = (
            "══════════════════════════════════════════════════════════\n"
            "SÉQUENCE D'ÉCRITURE OBLIGATOIRE — respecter cet ordre AVANT tout autre fichier :\n"
            + "\n".join(f"  {i+1}. {f}" for i, f in enumerate(_ordered))
            + "\n"
            "INTERDIT : run_build() ou tout fichier métier avant que TOUS ces fichiers soient écrits.\n"
            "══════════════════════════════════════════════════════════\n\n"
        )

    messages = [
        SystemMessage(content=prompt),
        HumanMessage(content=(
            f"Projet : {project_name}\n\n"
            f"{ordering_block}"
            f"{spec_degraded_block}"
            f"Spec :\n{summarized_spec}\n\n"
            f"Mermaid :\n{summarized_mermaid}\n\n"
            f"Contexte RAG obligatoire (préchargé) :\n{mandatory_rag_context}\n\n"
            f"{packages_block}"
            f"{dev_packages_block}"
            f"{templates_block}"
            f"{required_files_block}"
            f"{requirements_block}"
        ))
    ]
    runner = LLMConversationRunner(llm, messages)

    files = {}
    # Pré-populer files avec le contenu des templates (comptabilisés comme déjà écrits)
    files.update(_template_written)
    final_message = ""
    _final_gate_source = ""  # "structural" | "requirements" | "no_files" | "" (pas de blocage gate)
    _final_blocking_guard_id = ""  # id du guard qui a bloqué (ex: "use_client", "blueprint")
    _final_gate_message = ""  # message gate final (excerpt) pour observabilité
    _final_missing_required_files: list[str] = []  # détails blueprint quand blocage structural
    _guard_warning_hits: dict[str, int] = {}  # observabilité faux positifs potentiels (guards en mode warn)
    build_attempts = 0
    build_attempted = False
    build_success = False
    _sup_files_reviewed = 0
    _sup_corrections_count = 0
    _supervision_loop = FileSupervisionLoop(max_attempts=2)
    _conformity_scores: list[float] = []
    _security_scores: list[float] = []
    _architecture_scores: list[float] = []
    _build_corrections_count = 0
    last_build_succeeded = False  # True uniquement quand run_build() confirme un succès réel
    last_build_error = ""
    last_build_error_full = ""
    last_test_error = ""
    last_test_error_full = ""
    last_failed_command = ""

    def _extract_stderr(output: str) -> str:
        if not output:
            return ""
        marker = "STDERR:\n"
        if marker in output:
            return output.split(marker, 1)[1].strip()
        return ""

    def _extract_failed_command(output: str) -> str:
        match = re.search(r"Command failed \(code \d+\):\s*(\[[^\]]+\])", output)
        if not match:
            return ""
        raw_cmd = match.group(1)
        try:
            parsed = ast.literal_eval(raw_cmd)
            if isinstance(parsed, list):
                return " ".join(str(x) for x in parsed)
        except Exception:
            pass
        return raw_cmd

    _validator = PreBuildValidator(
        stack_cfg=stack_cfg,
        required_files=required_files,
        templated_names=_templated_names,
        supervision_loop=_supervision_loop,
        scaffold_extends_paths=scaffold_extends_paths,
        stack_id=effective_stack_id,
        guard_warning_hits=_guard_warning_hits,
    )

    _progress = ProgressSummary()

    def _build_run_state(files_dict: dict) -> dict:
        cov = _engine_compute_coverage_detailed(requirements or [], files_dict)
        unmet = sort_requirements_by_priority(cov.get("unmet", []), _path_priority_ranker)
        prisma_unmet = [
            r for r in unmet
            if ("modèle prisma" in str(r).lower() or "model prisma" in str(r).lower() or "prisma:" in str(r).lower())
        ]
        schema_text = str(files_dict.get("prisma/schema.prisma", "") or "")
        schema_has_model = bool(re.search(r"(?m)^\s*model\s+\w+\s*\{", schema_text))
        _present_p = {k.replace("\\", "/").lower() for k in files_dict.keys()}
        missing_files = sort_paths_by_priority(
            [p for p in llm_required_files
             if not any(pp == str(p).replace("\\", "/").lower() or pp.endswith("/" + str(p).replace("\\", "/").lower())
                        for pp in _present_p)],
            _path_priority_ranker,
        )
        structural_gid, structural_paths = _validator.find_blocking_targets(files_dict)
        # Priorité convergence: créer d'abord les fichiers blueprint manquants.
        # Sinon l'agent peut boucler sur des détails requirements sans jamais
        # produire le fichier racine attendu par le gate structural.
        if missing_files:
            missing_norm = [str(p).replace("\\", "/").lower() for p in missing_files]
            if "prisma/schema.prisma" in missing_norm:
                blocker = "file_missing::prisma/schema.prisma"
            elif prisma_unmet:
                # Priorité Prisma si des modèles manquent dans le schema,
                # même si d'autres modèles existent déjà (schema_has_model=True).
                # scaffold_extends accumule les blocs model — chaque write ajoute
                # les modèles manquants sans écraser les existants.
                # Note: la garde "not schema_has_model" a été retirée car elle
                # empêchait d'ajouter le premier modèle quand le second était déjà présent.
                blocker = f"requirements::{prisma_unmet[0]}"
            else:
                blocker = f"file_missing::{missing_files[0]}"
        elif structural_gid:
            blocker = f"structural::{structural_gid}"
        elif prisma_unmet:
            # Même logique hors missing_files.
            blocker = f"requirements::{prisma_unmet[0]}"
        elif unmet:
            blocker = f"requirements::{unmet[0]}"
        elif last_build_error:
            blocker = "build_error"
        else:
            blocker = "ready_for_build"
        return {
            "requirements_met": cov.get("requirements_met", 0),
            "requirements_total": cov.get("requirements_total", 0),
            "requirements_unmet": unmet,
            "requirements_statuses": cov.get("statuses", []),
            "missing_required_files": missing_files,
            "structural_blocking_guard_id": structural_gid,
            "structural_targets": structural_paths,
            "active_blocker": blocker,
            "last_build_error_excerpt": (last_build_error or "")[:400],
            "build_attempts": build_attempts,
            "iterations_left": max(0, MAX_ITERATIONS - iteration + 1),
        }

    stagnant_iterations = 0
    key_files = required_files or ["package.json"]

    # ── T004 : State Machine Déterministe ───────────────────────────────────────
    # États formels : GEN → STRUCT_GATES → REQ_GATES → BUILD → FINAL
    _SM_GEN = "GEN"
    _SM_STRUCT_GATES = "STRUCT_GATES"
    _SM_REQ_GATES = "REQ_GATES"
    _SM_BUILD = "BUILD"
    _SM_FINAL = "FINAL"
    _state = _SM_GEN
    logger.info(f"[STATE] initial → {_state}")

    # Budget token par phase depuis config (T004) — 1 token ≈ 4 chars
    _token_budgets = stack_cfg.get("token_budgets", {})
    _PHASE1_MAX_CHARS = int(_token_budgets.get("phase1_tokens", 6000) * 4)   # GEN
    _PHASE2_MAX_CHARS = int(_token_budgets.get("phase2_tokens", 14000) * 4)  # BUILD+
    logger.info(f"[STATE] token budgets — phase1={_PHASE1_MAX_CHARS} chars, phase2={_PHASE2_MAX_CHARS} chars")
    # ────────────────────────────────────────────────────────────────────────────

    def _append_aggregated_gate_warnings(msgs: list[str]) -> None:
        if not msgs:
            return
        unique_msgs = list(dict.fromkeys([m.strip() for m in msgs if str(m).strip()]))
        if not unique_msgs:
            return
        preview = unique_msgs[:3]
        more = len(unique_msgs) - len(preview)
        body = "\n\n".join(preview)
        if more > 0:
            body += f"\n\n... {more} warning(s) supplémentaire(s) non affiché(s) dans ce tour."
        messages.append(
            HumanMessage(
                content=(
                    "[PREBUILD WARNINGS AGGREGATED]\n"
                    "Warnings non bloquants détectés (agrégés, une seule notification par itération):\n\n"
                    f"{body}"
                )
            )
        )

    for iteration in range(1, MAX_ITERATIONS + 1):
        current_phase = 1 if iteration <= PHASE1_LIMIT else 2
        current_tools = tools_phase1 if current_phase == 1 else tools_phase2
        logger.info(f"[DEV AGENT v3.2] Itération {iteration}/{MAX_ITERATIONS} | Phase {current_phase} | State {_state} | Build attempts: {build_attempts}")

        # Ne plus muter l'historique complet (risque de perdre des contraintes).
        # Le budget est appliqué de façon déterministe par _main_context.
        if len(messages) > 28:
            logger.info("Historique long détecté — conservation intégrale, sélection contextuelle via _main_context.")

        # T004 — budget contexte par phase
        _ctx_budget = _PHASE1_MAX_CHARS if _state == _SM_GEN else _PHASE2_MAX_CHARS
        main_messages = runner._main_context(messages, max_chars=_ctx_budget)
        run_state = _build_run_state(files)
        _progress.update(run_state)
        main_messages.append(HumanMessage(content=build_iteration_brief(run_state, _progress, stack_cfg)))
        # Empêche les appels prématurés à run_build tant qu'un gate est actif.
        # Cela réduit les boucles "run_build -> gate blocked" sans progression d'écriture.
        _iter_tools = current_tools
        if run_state.get("active_blocker") != "ready_for_build":
            _iter_tools = [t for t in current_tools if getattr(t, "name", "") != "run_build"]
        response = llm.bind_tools(_iter_tools).invoke(main_messages)
        messages.append(response)

        tool_messages = []
        raw_tool_outputs = []
        iter_gate_warnings: list[str] = []
        successful_write_paths: set[str] = set()
        wrote_file_this_iter = False
        _wrote_pending_file_this_iter = False  # True si un fichier en attente superviseur a été réécrit
        called_build_this_iter = False
        build_failed_this_iter = False
        if response.tool_calls:
            for tool_call in response.tool_calls:
                tool_name = tool_call["name"]
                tool_to_call = tool_map.get(tool_name)
                if tool_to_call:
                    try:
                        # Hard rule: corrige project_dir pour run_build si le LLM passe '.'
                        # alors que les fichiers sont sous un sous-répertoire.
                        call_args = tool_call["args"]
                        if tool_name == "write_file":
                            _allowed = allowed_paths_for_blocker(run_state, scaffold_extends_paths)
                            _path = str(call_args.get("path", ""))
                            if not path_is_allowed_for_objective(
                                _path, _allowed, run_state.get("active_blocker", ""), scaffold_extends_paths
                            ):
                                logger.info(
                                    "[write_focus_block] blocker=%s path=%s allowed=%s",
                                    run_state.get("active_blocker", ""),
                                    _path,
                                    _allowed,
                                )
                                _allowed_msg = ", ".join(_allowed) if _allowed else "aucune restriction"
                                tool_messages.append(
                                    ToolMessage(
                                        content=(
                                            "WRITE_FILE BLOQUÉ (focus actif)\n"
                                            f"Objectif courant: {run_state.get('active_blocker', 'N/A')}\n"
                                            f"Chemin proposé: {_path}\n"
                                            f"Chemins autorisés: {_allowed_msg}\n"
                                            "Corrige d'abord la priorité active."
                                        ),
                                        tool_call_id=tool_call["id"],
                                    )
                                )
                                continue
                        # ── Template write-protection ────────────────────────────────────
                        # Les singletons de stack (lib/prisma.ts, middleware.ts, etc.) sont
                        # écrits par la factory AVANT la boucle LLM et sont corrects.
                        # Message neutre : évite de désorienter le LLM (run-05 lesson).
                        _tp_norm = _path.lstrip("./").replace("\\", "/")
                        if _tp_norm in _templated_names and _tp_norm not in scaffold_extends_paths:
                            logger.info(f"[template_guard] write ignoré pour template: {_path}")
                            tool_messages.append(
                                ToolMessage(
                                    content=f"[OK] '{_path}' déjà sur le disque (template factory). Passe au fichier suivant.",
                                    tool_call_id=tool_call["id"],
                                )
                            )
                            continue
                        if tool_name == "run_build":
                            computed_dir = find_project_dir(files, effective_stack_id)
                            if computed_dir != "." and call_args.get("project_dir", ".") == ".":
                                call_args = {**call_args, "project_dir": computed_dir}
                                logger.info(f"[run_build] project_dir corrigé: '.' → '{computed_dir}'")
                            # ── PRE-BUILD GATES (Blueprint + UseState + Prisma) ──────────────
                            # T004 — transition d'état explicite
                            _prev_state = _state
                            _state = _SM_STRUCT_GATES
                            logger.info(f"[STATE] {_prev_state} → {_state}")
                            _gate_blocked, _gate_msg, _, _gate_warns = _validator.check(files)
                            iter_gate_warnings.extend(_gate_warns)
                            if not _gate_blocked:
                                # ── DETERMINISTIC PRE-BUILD CHECKS (tsc + prisma validate) ──────
                                try:
                                    with ThreadPoolExecutor(max_workers=1) as _ex:
                                        _det_blocked, _det_msg = _ex.submit(
                                            asyncio.run,
                                            run_pre_build_deterministic_checks(_workdir),
                                        ).result()
                                except Exception as _det_exc:
                                    logger.debug(f"[pre_build_det] non-bloquant: {_det_exc}")
                                    _det_blocked, _det_msg = False, ""
                                if _det_blocked:
                                    _gate_blocked = True
                                    _gate_msg = _det_msg
                            if not _gate_blocked:
                                # ── REQUIREMENTS GATE ─────────────────────────────────────────
                                _prev_state = _state
                                _state = _SM_REQ_GATES
                                logger.info(f"[STATE] {_prev_state} → {_state}")
                                _gate_blocked, _gate_msg = _engine_gate_check(requirements or [], files)
                            if _gate_blocked:
                                tool_messages.append(ToolMessage(content=_gate_msg, tool_call_id=tool_call["id"]))
                                logger.warning(f"[PreBuildGate] BUILD BLOQUÉ (tool_call path)")
                                # build_attempted reste False : run_build n'a PAS été exécuté.
                                # Ne PAS considérer un build bloqué comme progrès:
                                # cela masque les boucles et retarde la convergence.
                                called_build_this_iter = False
                                continue  # ne pas exécuter run_build
                        logger.info(f"Exécution tool: {tool_name}")
                        # T004 — transition vers BUILD avant exécution réelle de run_build
                        if tool_name == "run_build":
                            _prev_state = _state
                            _state = _SM_BUILD
                            logger.info(f"[STATE] {_prev_state} → {_state}")
                        output = tool_to_call.invoke(call_args)
                        raw_output = str(output)
                        raw_tool_outputs.append(raw_output)
                        if tool_name == "write_file":
                            _wp = str(call_args.get("path", "")).replace("\\", "/").strip()
                            # Ne compter comme écrit que les write_file réellement réussis.
                            # Évite de polluer files[] avec du contenu non présent sur disque
                            # (ex: package.json invalide/refusé), ce qui fausse les gates.
                            if _wp and raw_output.startswith("OK:"):
                                successful_write_paths.add(_wp)

                        if tool_name == "run_build":
                            build_attempted = True
                            called_build_this_iter = True
                            if "Build successful" in raw_output:
                                last_build_succeeded = True  # build réel confirmé
                                build_success = True
                                build_attempts = 0
                                last_build_error = ""
                                last_build_error_full = ""
                                last_failed_command = ""
                            else:
                                build_failed_this_iter = True
                                extracted_stderr = _extract_stderr(raw_output)
                                last_build_error_full = extracted_stderr if extracted_stderr else raw_output
                                last_build_error = last_build_error_full[:2000]
                                failed_cmd = _extract_failed_command(raw_output)
                                if failed_cmd:
                                    last_failed_command = failed_cmd

                        if tool_name == "run_tests":
                            if "Tests passed" in raw_output:
                                last_test_error = ""
                                last_test_error_full = ""
                            else:
                                extracted_stderr = _extract_stderr(raw_output)
                                last_test_error_full = extracted_stderr if extracted_stderr else raw_output
                                last_test_error = last_test_error_full[:2000]

                        shrunk_output = runner._shrink_tool_output(tool_name, raw_output)
                        tool_messages.append(ToolMessage(content=shrunk_output, tool_call_id=tool_call["id"]))
                    except Exception as e:
                        error_text = f"ERREUR {tool_name}: {e}"
                        raw_tool_outputs.append(error_text)
                        if tool_name == "run_build":
                            build_attempted = True
                            called_build_this_iter = True
                            build_failed_this_iter = True
                            last_build_error = error_text[:2000]
                            last_build_error_full = error_text
                            last_failed_command = "run_build"
                        if tool_name == "run_tests":
                            last_test_error = error_text[:2000]
                            last_test_error_full = error_text
                        tool_messages.append(ToolMessage(content=error_text, tool_call_id=tool_call["id"]))
                else:
                    if tool_name == "run_build" and current_phase == 1:
                        tool_messages.append(
                            ToolMessage(
                                content="Génération non terminée, continue d'écrire les fichiers",
                                tool_call_id=tool_call["id"],
                            )
                        )
                    else:
                        tool_messages.append(ToolMessage(content=f"Tool {tool_name} inconnu", tool_call_id=tool_call["id"]))

            messages.extend(tool_messages)

            _files_to_supervise: list[tuple[str, str]] = []
            for tc in response.tool_calls:
                if tc["name"] == "write_file":
                    path = tc["args"].get("path")
                    content = tc["args"].get("content")
                    if path and content is not None:
                        _path_norm = str(path).replace("\\", "/").strip()
                        if _path_norm not in successful_write_paths:
                            logger.info(f"Write ignoré (non confirmé sur disque): {_path_norm}")
                            continue
                        # Lire le contenu réel depuis le disque pour garder
                        # files[path] aligné avec ce que les gates utiliseront.
                        _prev_content = files.get(path, "")
                        try:
                            workdir = os.getenv("FACTORY_WORKDIR", ".")
                            disk_path = os.path.normpath(os.path.join(workdir, path))
                            with open(disk_path, "r", encoding="utf-8") as _df:
                                files[path] = _df.read()
                        except Exception:
                            files[path] = content  # fallback si lecture échoue
                        file_content_on_disk = files.get(path, "")
                        # No-op detection : si le contenu disque n'a pas changé,
                        # ne pas déclencher reset_file ni re-supervision.
                        # Évite les boucles sur les fichiers scaffold_extends
                        # que le LLM réécrit sans modification réelle.
                        # Normalisation trailing whitespace avant comparaison :
                        # le scaffold_extends merge produit parfois des contenus
                        # identiques à 1 char près (trailing newline), ce qui cause
                        # 7+ rewrites non-noop et des oscillations 820/821 chars.
                        _is_noop_write = (
                            bool(_prev_content)
                            and _prev_content.rstrip() == file_content_on_disk.rstrip()
                        )
                        if _is_noop_write:
                            logger.info(f"[noop_write] {_path_norm} : contenu inchangé — supervision ignorée")
                        else:
                            wrote_file_this_iter = True
                            logger.info(f"Fichier généré : {path}")
                            # IMPORTANT Phase 1: ré-armer la boucle de supervision
                            # immédiatement après une écriture confirmée sur disque.
                            _supervision_loop.reset_file(_path_norm)
                            if file_content_on_disk:
                                # Si le fichier était en attente de re-vérification superviseur → noter la réécriture
                                if _path_norm in _supervision_loop.pending_paths():
                                    logger.info(f"[supervision_loop] {_path_norm} réécrit après correction superviseur")
                                    _wrote_pending_file_this_iter = True
                                _files_to_supervise.append((_path_norm, file_content_on_disk))

            # ── Supervision inline avec boucle de correction per-fichier ─────────────
            if _files_to_supervise:
                for _batch_start in range(0, len(_files_to_supervise), _supervision_batch_size):
                    _batch = _files_to_supervise[_batch_start:_batch_start + _supervision_batch_size]
                    _batch_t0 = time.perf_counter()
                    for _path_norm, file_content_on_disk in _batch:
                        supervisors_to_call = _match_supervision_routing_inline(_path_norm, _supervision_routing)
                        if not supervisors_to_call:
                            continue

                        # Si ce fichier était en attente de re-vérification → on re-supervise
                        _is_reverification = _supervision_loop.needs_reverification(_path_norm)
                        if _is_reverification:
                            logger.info(f"[supervision_loop] Re-vérification de {_path_norm} après correction")

                        _sup_files_reviewed += 1
                        _sup_context = {
                            "requirements": requirements or [],
                            "plan": plan or {},
                            "files_so_far": files,
                            "prisma_schema": files.get("prisma/schema.prisma", ""),
                            "project_name": project_name or "",
                            "run_id": run_id or "",
                            "stack_id": stack_id or "nextjs-clerk-prisma",
                        }
                        try:
                            with ThreadPoolExecutor(max_workers=1) as _ex:
                                _sup_result = _ex.submit(
                                    asyncio.run,
                                    _supervise_file_inline(
                                        _path_norm,
                                        file_content_on_disk,
                                        _sup_context,
                                        supervisors_to_call,
                                        _conformity_scores,
                                        _security_scores,
                                        _architecture_scores,
                                        timeout_ms=_supervisor_timeout_ms,
                                        project_dir=_workdir,
                                    ),
                                ).result()
                            _sup_msg, _sup_raw_results = _sup_result

                            if _sup_msg:
                                # Fichier nécessite une correction
                                should_inject = _supervision_loop.on_supervisor_needs_fix(_path_norm)
                                if should_inject:
                                    _sup_corrections_count += 1
                                    runner.inject(_sup_msg)
                                    logger.info(
                                        f"[supervision_loop] Correction injectée pour {_path_norm} "
                                        f"(tentatives restantes: {_supervision_loop._pending.get(_path_norm, 0)})"
                                    )
                                else:
                                    logger.info(f"[supervision_loop] {_path_norm}: max tentatives atteintes, correction ignorée")
                            else:
                                # Superviseurs OK
                                _supervision_loop.on_supervisor_ok(_path_norm)
                                if _is_reverification:
                                    logger.info(f"[supervision_loop] {_path_norm}: re-vérification OK — validé")

                            try:
                                _write_learner_event(
                                    event_type="supervisor_file_reviewed",
                                    payload={
                                        "file_path": _path_norm,
                                        "supervisors": supervisors_to_call,
                                        "is_reverification": _is_reverification,
                                        "results": {
                                            k: {
                                                "status": v.get("status"),
                                                "confidence": float(v.get("confidence", 0.0) or 0.0),
                                                "fix_applied": bool(
                                                    str(v.get("status", "")).lower() == "needs_fix"
                                                    and float(v.get("confidence", 0.0) or 0.0) > 0.7
                                                ),
                                            }
                                            for k, v in (_sup_raw_results or {}).items()
                                        },
                                        "project_name": project_name or "",
                                        "stack_id": stack_id or "nextjs-clerk-prisma",
                                    },
                                    run_id=run_id or "",
                                )
                            except Exception as _sl_err:
                                logger.warning(f"[inline_supervisor] shadow log non bloquant: {_sl_err}")
                        except Exception as _sup_err:
                            logger.warning(f"[inline_supervisor] non bloquant: {_sup_err}")
                    _batch_duration_ms = int((time.perf_counter() - _batch_t0) * 1000)
                    logger.info(
                        f"[inline_supervisor] batch_size={len(_batch)} duration_ms={_batch_duration_ms} "
                        f"timeout_ms={_supervisor_timeout_ms}"
                    )

        # Détection build succès/échec déterministe: uniquement depuis run_build.
        if build_failed_this_iter:
            build_attempts += 1
            if last_build_error_full:
                try:
                    with ThreadPoolExecutor(max_workers=1) as _ex:
                        _bs_result = _ex.submit(
                            asyncio.run,
                            _run_build_supervisor_inline(
                                last_build_error_full,
                                files,
                                run_id,
                                stack_id,
                            ),
                        ).result()
                    if _bs_result:
                        _build_corrections_count += 1
                        runner.inject(_bs_result)
                        logger.info("[build_supervisor] correction injectée dans la boucle")
                except Exception as _bs_err:
                    logger.warning(f"[build_supervisor] non bloquant: {_bs_err}")

        if called_build_this_iter:
            stagnant_iterations = 0
        elif wrote_file_this_iter:
            # Reset seulement si aucune correction superviseur n'est en attente
            # ou si le LLM a réécrit un fichier qui était en attente de correction.
            # Sinon (LLM réécrit des fichiers non-pending ex: schema.prisma en boucle) → stagnant.
            if not _supervision_loop.has_pending_corrections() or _wrote_pending_file_this_iter:
                stagnant_iterations = 0
            else:
                stagnant_iterations += 1
                logger.info(
                    f"[stagnant] LLM a écrit des fichiers mais pas les {len(_supervision_loop.pending_paths())} "
                    f"fichier(s) en attente superviseur — stagnant_iterations={stagnant_iterations}"
                )
        else:
            stagnant_iterations += 1

        # Vérification immédiate du blocker actif après écriture.
        if wrote_file_this_iter:
            _post_write_state = _build_run_state(files)
            _pre_blocker = run_state.get("active_blocker", "")
            _post_blocker = _post_write_state.get("active_blocker", "")
            if _pre_blocker and _pre_blocker == _post_blocker and _pre_blocker != "ready_for_build":
                _allowed = allowed_paths_for_blocker(_post_write_state, scaffold_extends_paths)
                _allowed_msg = ", ".join(_allowed) if _allowed else "aucune restriction"
                runner.inject((
                    "[IMMEDIATE_VERIFY] Le blocker actif n'a pas été résolu dans ce tour.\n"
                    f"Blocker courant: {_post_blocker}\n"
                    f"Chemins autorisés maintenant: {_allowed_msg}\n"
                    "Corrige ce blocker en priorité avant toute autre écriture."
                ))

        # ── Guard Phase 1 : primary_manifest DOIT être le premier fichier écrit ──────
        # Lecture depuis stack config (multi-stack safe) au lieu de hardcoder "package.json".
        _primary = get_root_file(stack_id) if stack_id else "package.json"
        if current_phase == 1 and wrote_file_this_iter and _primary not in files:
            non_pkg_files = [
                tc["args"].get("path", "")
                for tc in response.tool_calls
                if tc["name"] == "write_file" and tc["args"].get("path", "") != _primary
            ]
            if non_pkg_files:
                logger.warning(
                    f"[PHASE1_SEQUENCE_VIOLATION] Fichier(s) écrit(s) avant {_primary} : {non_pkg_files}"
                )
                runner.inject((
                    f"⚠️ ERREUR DE SÉQUENCE CRITIQUE : Tu as écrit {non_pkg_files} avant {_primary}.\n"
                    f"RÈGLE ABSOLUE : {_primary} DOIT être le PREMIER fichier généré, AVANT TOUT AUTRE.\n"
                    f"ACTION OBLIGATOIRE IMMÉDIATE : génère {_primary} maintenant avec les versions exactes :\n"
                    + "\n".join(f'  "{pkg}": "{ver}"' for pkg, ver in packages.items())
                    + f"\n\nNe génère AUCUN autre fichier avant que {_primary} soit écrit."
                ))

        # Forçage progression si fichiers clés présents
        _pdir = find_project_dir(files, effective_stack_id)  # Hard rule: répertoire réel du projet
        _files_norm = {p.replace("\\", "/").lower() for p in files}
        if all(
            any(
                fp == k.replace("\\", "/").lower() or fp.endswith("/" + k.replace("\\", "/").lower())
                for fp in _files_norm
            )
            for k in key_files
        ) and not build_success:
            # Ordre: d'abord les gates structurelles (_validator.check), puis requirements.
            # Garantit que le LLM reçoit le feedback le plus proche du blocage réel.
            _early_gates_blocked, _early_gates_msg, _, _early_gate_warns = _validator.check(files)
            iter_gate_warnings.extend(_early_gate_warns)
            if _early_gates_blocked:
                runner.inject(f"[PRE_BUILD_CHECK]\n{_early_gates_msg}")
            else:
                _rg_early_blocked, _rg_early_msg = _engine_gate_check(requirements or [], files)
                if _rg_early_blocked:
                    runner.inject(f"[REQUIREMENTS CHECK]\n{_rg_early_msg}")
                else:
                    runner.inject(f"Fichiers clés présents. Appelle run_build(project_dir='{_pdir}') maintenant pour valider le projet.")

        # Garde-fou: si le modele stagne sans progres, forcer un run_build.
        if not build_success and not called_build_this_iter and (stagnant_iterations >= 2 or iteration >= MAX_ITERATIONS - 1):
            # ── Même gates pré-build que le chemin tool_call ──────────────────
            # bypass_supervision=True: si l'agent stagne malgré les corrections superviseurs,
            # on force le build en best-effort pour débloquer la boucle.
            _bypass_sup = stagnant_iterations >= 2 and _supervision_loop.has_pending_corrections()
            if _bypass_sup:
                # Force-valider les fichiers pending : le LLM n'a pas appliqué
                # les corrections dans les itérations imparties → best-effort.
                # Sans ce clear, le requirements gate peut encore bloquer si
                # les fichiers pending contiennent des données nécessaires
                # (ex: schema.prisma avec Habit model non détecté à cause
                # d'une oscillation trailing-newline).
                for _bp_path in list(_supervision_loop.pending_paths()):
                    _supervision_loop.on_supervisor_ok(_bp_path)
                logger.warning(
                    f"[supervision_loop] BYPASS — corrections pendantes force-validées en best-effort "
                    f"après {stagnant_iterations} itérations stagnantes"
                )
            _forced_blocked, _forced_msg, _, _forced_gate_warns = _validator.check(files, bypass_supervision=_bypass_sup)
            iter_gate_warnings.extend(_forced_gate_warns)
            if not _forced_blocked:
                _forced_blocked, _forced_msg = _engine_gate_check(requirements or [], files)
            if _forced_blocked:
                runner.inject(f"[PRE_BUILD_CHECK]\n{_forced_msg}")
                logger.warning(f"[PreBuildGate] FORCED BUILD BLOQUÉ — fichiers manquants ou violations")
                stagnant_iterations = 0  # reset pour laisser l'agent corriger
            else:
                forced_build_output = str(run_build.invoke({"project_dir": _pdir}))
                build_attempted = True
                called_build_this_iter = True
                raw_tool_outputs.append(forced_build_output)
                runner.inject(f"[FORCED_RUN_BUILD]\n{runner._shrink_tool_output('run_build', forced_build_output)}")
                if "Build successful" in forced_build_output:
                    last_build_succeeded = True  # build réel confirmé (chemin forcé)
                    build_success = True
                    build_attempts = 0
                    last_build_error = ""
                    last_build_error_full = ""
                    last_failed_command = ""
                else:
                    build_attempts += 1
                    extracted_stderr = _extract_stderr(forced_build_output)
                    last_build_error_full = extracted_stderr if extracted_stderr else forced_build_output
                    last_build_error = last_build_error_full[:2000]
                    failed_cmd = _extract_failed_command(forced_build_output)
                    if failed_cmd:
                        last_failed_command = failed_cmd
                    try:
                        with ThreadPoolExecutor(max_workers=1) as _ex:
                            _bs_result = _ex.submit(
                                asyncio.run,
                                _run_build_supervisor_inline(
                                    last_build_error_full,
                                    files,
                                    run_id,
                                    stack_id,
                                ),
                            ).result()
                        if _bs_result:
                            _build_corrections_count += 1
                            runner.inject(_bs_result)
                            logger.info("[build_supervisor] correction injectée après FORCED_RUN_BUILD")
                    except Exception as _bs_err:
                        logger.warning(f"[build_supervisor] non bloquant (forced): {_bs_err}")

        _append_aggregated_gate_warnings(iter_gate_warnings)

        # Reflection informative uniquement (ne pilote pas la sortie).
        _reflection_state = _build_run_state(files)
        _reflection_unmet = _reflection_state.get("requirements_unmet", [])
        _reflection_missing = _reflection_state.get("missing_required_files", [])
        reflection_messages = [
            SystemMessage(content=(
                "État actuel :\n"
                f"Requirements couverts : {_reflection_state.get('requirements_met', 0)}/{_reflection_state.get('requirements_total', 0)}\n"
                f"Blocker actif : {_reflection_state.get('active_blocker', 'N/A')}\n"
                f"Requirement prioritaire non couvert : {_reflection_unmet[0] if _reflection_unmet else 'N/A'}\n"
                f"Fichier requis manquant prioritaire : {_reflection_missing[0] if _reflection_missing else 'N/A'}\n"
                f"Build attempts : {build_attempts}/{MAX_BUILD_ATTEMPTS}\n"
                f"Dernière erreur build : {last_build_error[:500] if last_build_error else 'N/A'}\n"
                f"Dernière commande en échec : {last_failed_command or 'N/A'}\n"
                "- Si 'Build successful' dans les logs → réponds 'TERMINÉ : CODE PRÊT'\n"
                "- Si trop d'échecs → 'ÉCHEC : ERREUR RÉCURRENTE BUILD'\n"
                "- Sinon → continue l'étape suivante sans réécrire les fichiers existants."
            )),
            HumanMessage(content=(
                f"Résumé runtime: blocker={_reflection_state.get('active_blocker', 'N/A')}, "
                f"requirements={_reflection_state.get('requirements_met', 0)}/{_reflection_state.get('requirements_total', 0)}"
            ))
        ]

        # PAS de bind_tools sur la reflection — juste du texte
        reflection_response = llm.invoke(reflection_messages)
        reflection = reflection_response.content.strip()
    # Pas besoin de gérer tool_calls ici — llm.invoke sans tools ne peut pas en générer

        if hasattr(reflection_response, "tool_calls") and reflection_response.tool_calls:
            logger.warning("Reflection a généré des tool_calls inattendus → ignorés pour sécurité")
            # Do not append placeholder ToolMessages to the main 'messages' list.
            # This was the source of the persistent BadRequestError.

        runner.inject(reflection)
        # T004 — final_message calculé par état (jamais depuis texte LLM).
        # La reflection guide le LLM dans le tour suivant, elle n'est PAS final_message.

        # Sortie déterministe: uniquement sur résultat build confirmé.
        if last_build_succeeded:
            _state = _SM_FINAL
            logger.info(f"[STATE] BUILD → {_state} | BUILD_SUCCESS")
            build_success = True
            final_message = "BUILD_SUCCESS"
            break

        if build_attempts >= MAX_BUILD_ATTEMPTS:
            _state = _SM_FINAL
            logger.info(f"[STATE] {_state} → FINAL | BUILD_FAILED (max attempts)")
            final_message = "BUILD_FAILED"
            break

    # T004 — MAX_ITER_REACHED si la boucle s'est terminée sans break explicite
    if not build_success and _state != _SM_FINAL:
        _state = _SM_FINAL
        logger.info(f"[STATE] → {_state} | MAX_ITER_REACHED")
        final_message = "MAX_ITER_REACHED"

    # Terminal guard: un run ne doit jamais sortir sans tentative de build.
    _terminal_guard_handled = False
    if not build_attempted and files:
        _terminal_guard_handled = True
        _tg_dir = find_project_dir(files, effective_stack_id)
        _tg_blocked, _tg_msg, _tg_gid, _ = _validator.check(files)
        _tg_is_structural = _tg_blocked
        if not _tg_blocked:
            _tg_blocked, _tg_msg = _engine_gate_check(requirements or [], files)
            _tg_gid = "requirements" if _tg_blocked else ""
        if _tg_blocked:
            # T005 — final_message canonique. Détail dans les logs.
            final_message = "NOT_BUILT_BY_GATE"
            _final_gate_source = "structural" if _tg_is_structural else "requirements"
            _final_blocking_guard_id = _tg_gid
            _final_gate_message = (_tg_msg or "")[:2000]
            if _tg_gid == "blueprint":
                _present = set(files.keys()) | _templated_names
                _present_norm = {p.replace("\\", "/").lower() for p in _present}
                _final_missing_required_files = [
                    f
                    for f in required_files
                    if not any(
                        pp == str(f).replace("\\", "/").lower()
                        or pp.endswith("/" + str(f).replace("\\", "/").lower())
                        for pp in _present_norm
                    )
                ]
            logger.warning(f"[terminal_guard] build non tente: gate bloque. guard={_tg_gid} detail={_tg_msg[:400]}")
        else:
            forced_build_output = str(run_build.invoke({"project_dir": _tg_dir}))
            build_attempted = True
            logger.info("[terminal_guard] run_build force hors boucle LLM")
            if "Build successful" in forced_build_output:
                last_build_succeeded = True
                build_success = True
                final_message = "BUILD_SUCCESS"  # T005
                last_build_error = ""
                last_build_error_full = ""
                last_failed_command = ""
            else:
                _tg_stderr = _extract_stderr(forced_build_output)
                last_build_error_full = _tg_stderr if _tg_stderr else forced_build_output
                last_build_error = last_build_error_full[:2000]
                _tg_cmd = _extract_failed_command(forced_build_output)
                if _tg_cmd:
                    last_failed_command = _tg_cmd
                final_message = "BUILD_FAILED"  # T005

    if not _terminal_guard_handled and not build_attempted and not build_success:
        _state = _SM_FINAL
        final_message = "NOT_BUILT_BY_GATE"
        _final_gate_source = "no_files"
        _final_gate_message = "Aucun fichier généré; build non tentée."
        logger.info(f"[STATE] → {_state} | NOT_BUILT_BY_GATE (aucun fichier généré)")

    # Nettoyage scopé au répertoire projet — artifacts lus depuis stack config (multi-stack safe).
    _rel_dir = find_project_dir(files, effective_stack_id)
    _base = _workdir if _workdir else os.getcwd()
    project_abs = os.path.normpath(os.path.join(_base, _rel_dir))
    for _artifact in get_cleanup_artifacts(stack_id) if stack_id else [".next", "node_modules"]:
        shutil.rmtree(os.path.join(project_abs, _artifact), ignore_errors=True)
    shutil.rmtree(os.path.join(project_abs, "__pycache__"), ignore_errors=True)

    # Création du fichier de méta-données du run dans le répertoire projet.
    try:
        meta = {
            "run_id": run_id,
            "stack_id": effective_stack_id,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "workflow_version": "sprint3",
        }
        meta_path = os.path.join(project_abs, ".factory-meta.json")
        with open(meta_path, "w", encoding="utf-8") as _mf:
            json.dump(meta, _mf, indent=2)
        logger.info(f"[meta] .factory-meta.json créé : run_id={run_id}")
    except Exception as _me:
        logger.warning(f"[meta] Impossible de créer .factory-meta.json: {_me}")

    logger.info("Dev Agent v3.2 terminé.")
    _state_manager = BuildStateManager(
        iteration=iteration,
        build_attempts=build_attempts,
        build_attempted=build_attempted,
        build_success=build_success,
        final_message=final_message,
        gate_source=_final_gate_source,
        blocking_guard_id=_final_blocking_guard_id,
        gate_message=_final_gate_message,
        missing_required_files=_final_missing_required_files,
        guard_warning_hits=_guard_warning_hits,
        supervisor_files_reviewed=_sup_files_reviewed,
        supervisor_corrections_count=_sup_corrections_count,
        conformity_scores=list(_conformity_scores),
        security_scores=list(_security_scores),
        architecture_scores=list(_architecture_scores),
        build_corrections_count=_build_corrections_count,
        last_build_error=last_build_error,
        last_build_error_full=last_build_error_full,
        last_test_error=last_test_error,
        last_test_error_full=last_test_error_full,
        last_failed_command=last_failed_command,
    )
    return {
        "files": files,
        "final_message": final_message,
        "success": build_success,
        "metadata": _state_manager.to_metadata(
            total_files=len(files),
            supervision_loop_corrections=_supervision_loop.corrections_count,
            supervision_loop_pending_at_end=len(_supervision_loop.pending_paths()),
        ),
    }
