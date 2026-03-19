import os
import json
import logging
import shutil
import re
import ast
from pathlib import PurePosixPath
from datetime import datetime, timezone
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage

# Import des shared tools
from .shared_tools import (
    write_file,
    validate_syntax,
    prisma_migrate,
    rag_search,
    read_files,
    run_build,
    get_stack_id,
)
from .stack_config import (
    get_blueprint,
    get_root_file,
    get_cleanup_artifacts,
    get_workdir_keep_extra,
    get_forbidden_paths,
    get_forbidden_imports,
)
from utils.prompt_loader import load_stack_prompt
from .requirements_engine import (
    gate_check as _engine_gate_check,
    compute_coverage_detailed as _engine_compute_coverage_detailed,
)

# Logger
logger = logging.getLogger(__name__)
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")


def _collect_forbidden_import_violations(
    files_dict: dict,
    forbidden_tokens: list[str],
    templated_names: set[str] | None = None,
) -> list[tuple[str, str]]:
    """Retourne les violations (path, token) pour les imports/patterns interdits."""
    templated = templated_names or set()
    tokens = [str(t).strip() for t in (forbidden_tokens or []) if str(t).strip()]
    if not tokens:
        return []
    violations: list[tuple[str, str]] = []
    for fp, fc in files_dict.items():
        fp_norm = fp.replace("\\", "/")
        if fp_norm in templated:
            continue
        if not fp_norm.endswith((".ts", ".tsx", ".js", ".jsx")):
            continue
        content_lower = (fc or "").lower()
        for tok in tokens:
            if tok.lower() in content_lower:
                violations.append((fp_norm, tok))
                break
    return violations


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
        except:
            return text[:int(max_tokens * 3.5)] + "\n\n[TRUNCATED]"

    def _compact(text: str) -> str:
        """Compacte les espaces pour réduire la taille sans perdre l'information utile."""
        return re.sub(r"\s+", " ", text).strip()

    def _shrink_tool_output(tool_name: str, output: str, max_chars: int = MAX_TOOL_OUTPUT_CHARS) -> str:
        """
        Réduit les sorties tools avant insertion dans l'historique du LLM.
        Conserve début+fin, là où les erreurs importantes apparaissent souvent.
        """
        compact = _compact(output)
        if len(compact) <= max_chars:
            return compact
        head = max_chars // 2
        tail = max_chars - head
        return (
            f"[{tool_name}] OUTPUT_TRUNCATED total_chars={len(compact)} | "
            f"head: {compact[:head]} ... tail: {compact[-tail:]}"
        )

    def _main_context(messages_list, max_chars: int = MAX_MAIN_HISTORY_CHARS):
        """
        Contexte compact state-first:
        - garde les 2 messages initiaux,
        - garde UNIQUEMENT le dernier tour complet AI(tool_calls)+ToolMessages,
        - sinon garde le dernier message non-tool.
        Cela réduit le bruit et force la boucle done/missing/next.
        """
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

                # Ne garder que les turns complets (assistant + toutes réponses tools).
                if expected_ids and expected_ids.issubset(got_ids):
                    turns.append(turn)
                else:
                    logger.warning("Turn incomplet tool_calls ignoré dans _main_context")
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
            # Fallback: garder seulement le dernier message non-tool.
            for msg in reversed(messages_list[2:]):
                if not isinstance(msg, ToolMessage):
                    return kept + [msg]
            return kept
        return kept + last_turn

    summarized_spec = summarize_text(spec, MAX_SPEC_TOKENS, "Specification")
    summarized_mermaid = summarize_text(mermaid, MAX_MERMAID_TOKENS, "Mermaid Diagram")

    effective_stack_id = stack_id or get_stack_id()
    prompt = load_stack_prompt("dev", effective_stack_id)
    from .stack_config import load_stack_config
    stack_cfg = load_stack_config(effective_stack_id) or {}

    generation_order_cfg = stack_cfg.get("generation_order", {}) if isinstance(stack_cfg, dict) else {}
    _priority_paths_cfg = generation_order_cfg.get("priority_paths", []) if isinstance(generation_order_cfg, dict) else []
    PRIORITY_PATHS = [str(p).replace("\\", "/").strip() for p in _priority_paths_cfg if str(p).strip()]

    def _path_priority_rank(path: str) -> int:
        p = str(path or "").replace("\\", "/").strip().lower()
        if not PRIORITY_PATHS:
            return 10_000
        for idx, raw_pat in enumerate(PRIORITY_PATHS):
            pat = raw_pat.lower()
            if pat.endswith("/"):
                if p.startswith(pat):
                    return idx
            elif p == pat or p.endswith("/" + pat):
                return idx
        return 10_000 + len(PRIORITY_PATHS)

    def _sort_paths_by_priority(paths: list[str]) -> list[str]:
        return sorted(
            [str(p) for p in (paths or [])],
            key=lambda p: (_path_priority_rank(p), str(p).replace("\\", "/").lower()),
        )

    def _resolve_max_iterations(cfg: dict, reqs: list | None) -> int:
        policy = cfg.get("iteration_policy", {}) if isinstance(cfg, dict) else {}
        if not isinstance(policy, dict):
            return DEFAULT_MAX_ITERATIONS
        try:
            base = int(policy.get("base_max_iterations", DEFAULT_MAX_ITERATIONS))
        except Exception:
            base = DEFAULT_MAX_ITERATIONS
        try:
            cap = int(policy.get("max_cap_iterations", base))
        except Exception:
            cap = base
        if cap < 1:
            cap = base if base >= 1 else DEFAULT_MAX_ITERATIONS
        req_count = len(reqs or [])
        target = base
        tiers = policy.get("tiers", [])
        def _safe_int(v, d=0):
            try:
                return int(v)
            except Exception:
                return d

        if isinstance(tiers, list):
            for tier in sorted(
                [t for t in tiers if isinstance(t, dict)],
                key=lambda t: _safe_int(t.get("min_requirements", 0), 0),
            ):
                try:
                    min_req = int(tier.get("min_requirements", 0))
                    iter_cap = int(tier.get("max_iterations", target))
                except Exception:
                    continue
                if req_count >= min_req:
                    target = iter_cap
        target = max(1, target)
        target = min(target, cap)
        return target

    MAX_ITERATIONS = _resolve_max_iterations(stack_cfg, requirements)
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
    llm_required_files = _sort_paths_by_priority([f for f in required_files if f not in _templated_protected])
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

    def _first_directive_line(content: str, ignore_leading_comments: bool = False) -> str:
        """
        Retourne la première ligne sémantique candidate pour une directive de fichier.
        Optionnellement, ignore les commentaires d'en-tête (// et /* ... */).
        """
        if not content:
            return ""
        if not ignore_leading_comments:
            return next((ln.strip() for ln in content.splitlines() if ln.strip()), "")

        in_block_comment = False
        for raw_line in content.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            if in_block_comment:
                if "*/" in line:
                    in_block_comment = False
                continue
            if line.startswith("/*"):
                if "*/" not in line:
                    in_block_comment = True
                continue
            if line.startswith("//"):
                continue
            return line
        return ""

    def _find_project_dir(files_dict: dict) -> str:
        """
        Déduit le répertoire racine du projet à partir des fichiers écrits.
        Hard rule (couche Code) : si le LLM a écrit sous un sous-répertoire
        (ex: 'my-saas/package.json'), retourne ce sous-répertoire ('my-saas').
        Sinon retourne '.'. Corrige le bug working-directory FORCED_RUN_BUILD.
        Le fichier racine de référence est lu depuis la stack config (root_file),
        ce qui rend la détection compatible avec toutes les stacks futures.
        """
        try:
            from agents.stack_config import get_root_file
            root_file = get_root_file(effective_stack_id)
        except Exception:
            root_file = "package.json"
        root_filename = root_file.split("/")[-1]
        for p in files_dict.keys():
            normalized = p.replace("\\", "/")
            if normalized == root_file or normalized.endswith("/" + root_filename):
                parent = normalized.rsplit("/", 1)[0] if "/" in normalized else ""
                return parent if parent else "."
        return "."

    def _prebuild_gates(files_dict: dict) -> tuple:
        """
        Vérifie les conditions pré-build (Blueprint + UseState + Prisma import).
        Retourne (bloqué: bool, message: str).
        Utilisé sur DEUX chemins : tool_call run_build ET forced build.
        """
        import shutil as _shutil  # utilisé par les AST guards ("engine": "ast")
        _warnings: list[str] = []

        # 1. Blueprint Validator
        _present = set(files_dict.keys()) | _templated_names
        _present_norm = {p.replace("\\", "/").lower() for p in _present}
        _missing = []
        for f in required_files:
            f_norm = str(f).replace("\\", "/").lower()
            if not any(pp == f_norm or pp.endswith("/" + f_norm) for pp in _present_norm):
                _missing.append(f)
        if _missing:
            return True, (
                "BLUEPRINT VALIDATOR — BUILD BLOQUÉ\n"
                f"{len(_missing)} fichier(s) obligatoire(s) manquant(s) :\n"
                + "\n".join(f"  - {f}" for f in _missing)
                + "\n\nGénère ces fichiers avec write_file() maintenant."
                " run_build sera disponible une fois tous présents."
            ), "blueprint", _warnings
        # 2. PATH GUARDS — config-driven (naming conventions de fichiers/chemins)
        for _pg in stack_cfg.get("path_guards", []):
            _pg_id = str(_pg.get("id", "unknown"))
            _pg_kind = str(_pg.get("kind", "")).strip()
            _pg_mode = str(_pg.get("mode", "warn")).strip().lower()
            if _pg_mode not in ("warn", "block"):
                _pg_mode = "warn"
            _pg_msg_lines = _pg.get("message_lines", [f"{_pg_id} PATH GUARD", "{details}"])

            _violations: list[tuple[str, str]] = []  # (file_path, suggested_fix)

            if _pg_kind == "app_router_convention":
                _root = str(_pg.get("route_root", "app/"))
                _exts = tuple(_pg.get("file_extensions", [".tsx"]))
                _valid_route_names = set(_pg.get("valid_route_names", ["layout", "page", "error", "loading", "not-found", "template", "default"]))
                _excluded_dirs = set(_pg.get("excluded_directories", ["components", "lib", "utils", "hooks", "styles", "types", "context", "providers", "helpers"]))
                for _fp in files_dict.keys():
                    _p = PurePosixPath(_fp.replace("\\", "/"))
                    _fp_norm = str(_p)
                    if not _fp_norm.startswith(_root):
                        continue
                    if _p.suffix not in _exts:
                        continue
                    if len(_p.parts) >= 3 and _p.parts[1] in _excluded_dirs:
                        continue
                    if _p.stem in _valid_route_names:
                        continue
                    _suggested = str(_p.parent / _p.stem / "page.tsx")
                    _violations.append((_fp_norm, _suggested))

            elif _pg_kind == "app_router_api_naming":
                _api_root = str(_pg.get("api_root", "app/api/"))
                _exts = tuple(_pg.get("file_extensions", [".ts", ".tsx"]))
                _valid_stem = str(_pg.get("api_valid_stem", "route"))
                for _fp in files_dict.keys():
                    _p = PurePosixPath(_fp.replace("\\", "/"))
                    _fp_norm = str(_p)
                    if not _fp_norm.startswith(_api_root):
                        continue
                    if _p.suffix not in _exts:
                        continue
                    if _p.stem == _valid_stem:
                        continue
                    _suggested = str(_p.parent / "route.ts") if _p.stem == "index" else str(_p.parent / _p.stem / "route.ts")
                    _violations.append((_fp_norm, _suggested))

            if _violations:
                _details = "\n".join(f"  - {fp}  →  {suggested}" for fp, suggested in _violations)
                _msg = "\n".join(_pg_msg_lines).replace("{details}", _details)
                if _pg_mode == "warn":
                    _guard_warning_hits[_pg_id] = _guard_warning_hits.get(_pg_id, 0) + len(_violations)
                    logger.warning(f"[PATH_GUARD WARN {_pg_id}] {len(_violations)} violation(s)")
                    _warnings.append(f"[PATH_GUARD WARNING:{_pg_id}]\n{_msg}")
                else:
                    return True, _msg, _pg_id, _warnings

        # 3. FORBIDDEN PATHS GUARD (depuis stack config)
        _forbidden = get_forbidden_paths(stack_id) if stack_id else ["pages/", "src/pages/"]
        _forbidden_violations = [
            fp.replace("\\", "/")
            for fp in files_dict.keys()
            if any(fp.replace("\\", "/").startswith(f) for f in _forbidden)
        ]
        if _forbidden_violations:
            return True, (
                "FORBIDDEN PATHS GUARD — BUILD BLOQUÉ\n"
                "Fichiers détectés dans un chemin interdit (Pages Router au lieu de App Router) :\n"
                + "\n".join(f"  - {f}" for f in _forbidden_violations)
                + "\n\nCORRECTION OBLIGATOIRE — App Router UNIQUEMENT :\n"
                "INTERDIT: pages/api/<resource>/index.ts  →  CORRECT: app/api/<resource>/route.ts\n"
                "INTERDIT: pages/api/<resource>/[id].ts  →  CORRECT: app/api/<resource>/[id]/route.ts\n"
                "Structure App Router API :\n"
                "  app/api/<resource>/route.ts            → export async function GET() / POST()\n"
                "  app/api/<resource>/[id]/route.ts       → export async function GET() / PUT() / DELETE()\n"
                "Crée les fichiers App Router corrects avec write_file(), puis rappelle run_build."
            ), "forbidden_paths", _warnings
        # 6bis. FORBIDDEN IMPORTS GUARD (depuis stack config)
        _forbidden_import_tokens = get_forbidden_imports(stack_id) if stack_id else []
        _forbidden_import_violations = _collect_forbidden_import_violations(
            files_dict,
            _forbidden_import_tokens,
            templated_names=_templated_names,
        )
        if _forbidden_import_violations:
            _details = "\n".join(
                f"  - {fp}  (token: {tok})" for fp, tok in _forbidden_import_violations
            )
            _warn_msg = (
                "FORBIDDEN IMPORTS WARNING — NON BLOQUANT\n"
                "Des imports/patterns interdits par la stack ont été détectés :\n"
                f"{_details}\n\n"
                "Corrige les imports selon les règles stack (auth/ORM/UI), puis rappelle run_build."
            )
            logger.warning(f"[PREBUILD WARN forbidden_imports] {len(_forbidden_import_violations)} violation(s)")
            _warnings.append(f"[PREBUILD WARNING:forbidden_imports]\n{_warn_msg}")
        # 8+. CONTENT GUARDS — config-driven (T008/T009 multi-stack)
        # Toutes les règles de contenu fichier sont déclarées dans la section
        # "content_guards" du JSON de stack. dev.py ne contient aucune logique
        # spécifique à un framework — il lit et applique ces règles génériquement.
        #
        # Schéma d'une entrée content_guard :
        #   id                     : identifiant lisible (pour les logs)
        #   file_prefix            : filtrer les fichiers commençant par ce préfixe (ex: "app/")
        #   file_extensions        : filtrer par extension (ex: [".tsx", ".ts"])
        #   trigger_contains       : liste de sous-chaînes — déclenche si l'une est présente
        #   requires_first_directive: chaîne sémantique dont la présence en 1ère ligne annule
        #                            le déclenchement (ex: "use client"). None = pas de check.
        #   message_lines          : lignes du message constructif, "{details}" = liste fichiers.
        for _guard in stack_cfg.get("content_guards", []):
            _gid = _guard.get("id", "unknown")
            _engine = str(_guard.get("engine", "regex")).strip().lower()

            # ── P3 : Engine AST (ts-morph / Semgrep) ─────────────────────────
            # Infrastructure stub : quand Dockerfile inclura ts-morph/Semgrep,
            # chaque guard "engine": "ast" appellera un subprocess ici.
            # En attendant : fallback warn avec signal clair dans les logs.
            if _engine == "ast":
                _ast_tool = _guard.get("ast_tool", "ts-morph")  # "ts-morph" | "semgrep"
                _tool_binary = "node" if _ast_tool == "ts-morph" else "semgrep"
                if _shutil.which(_tool_binary) is None:
                    logger.warning(
                        f"[AST_GUARD {_gid}] {_ast_tool} non disponible "
                        f"('{_tool_binary}' introuvable dans PATH) — guard skippé. "
                        f"Ajouter {_ast_tool} au Dockerfile pour activer ce guard."
                    )
                    _warnings.append(f"[AST_GUARD SKIPPED:{_gid}] {_ast_tool} non disponible")
                else:
                    # Placeholder : sera complété par Codex (P3 infrastructure)
                    logger.info(f"[AST_GUARD {_gid}] {_ast_tool} disponible — exécution à implémenter (P3)")
                    _warnings.append(f"[AST_GUARD TODO:{_gid}] subprocess {_ast_tool} non encore câblé")
                continue  # AST guard traité (ou skippé) — pas de regex fallback

            _file_prefix = _guard.get("file_prefix", "")
            _file_exts = _guard.get("file_extensions", [])
            _triggers = _guard.get("trigger_contains", [])
            _trigger_regexes = _guard.get("trigger_regex", [])
            _requires_contains_all = _guard.get("requires_contains_all", []) or []
            _requires_regex_all = _guard.get("requires_regex_all", []) or []
            _directive = _guard.get("requires_first_directive")    # None = pas de vérif ; fire si ABSENTE
            _conflicts = _guard.get("conflicts_with_directive")    # None = pas de vérif ; fire si PRÉSENTE
            _ignore_leading_comments = bool(_guard.get("ignore_leading_comments", False))
            _mode = str(_guard.get("mode", "block")).strip().lower()
            if _mode not in ("block", "warn"):
                _mode = "block"
            _exclude_paths = [str(p).replace("\\", "/") for p in (_guard.get("exclude_paths", []) or [])]
            _exclude_when_contains = [str(s) for s in (_guard.get("exclude_when_contains", []) or [])]
            _msg_lines = _guard.get("message_lines", [f"{_gid} GUARD — BUILD BLOQUÉ", "{details}"])
            _compiled_regexes: list[tuple[str, re.Pattern]] = []
            for _rx in _trigger_regexes:
                try:
                    _compiled_regexes.append((str(_rx), re.compile(str(_rx), re.MULTILINE)))
                except re.error as _rx_err:
                    logger.warning(f"[CONTENT_GUARD {_gid}] regex invalide ignorée: {_rx} ({_rx_err})")
            _compiled_required_regexes: list[tuple[str, re.Pattern]] = []
            for _rx in _requires_regex_all:
                try:
                    _compiled_required_regexes.append((str(_rx), re.compile(str(_rx), re.MULTILINE)))
                except re.error as _rx_err:
                    logger.warning(f"[CONTENT_GUARD {_gid}] requires_regex_all invalide ignorée: {_rx} ({_rx_err})")

            _violations = []
            for _fp, _fc in files_dict.items():
                _fp_norm = _fp.replace("\\", "/")
                # Exclure les fichiers templates — leur contenu est validé en amont,
                # ils peuvent légitimement contenir des patterns que les guards détectent
                # (ex: lib/prisma.ts contient new PrismaClient() dans le singleton).
                if _fp_norm in _templated_names:
                    continue
                if any(_fp_norm.startswith(_xp) for _xp in _exclude_paths):
                    continue
                if _file_prefix and not _fp_norm.startswith(_file_prefix):
                    continue
                if _file_exts and not any(_fp_norm.endswith(ext) for ext in _file_exts):
                    continue
                if _exclude_when_contains and any(_needle in _fc for _needle in _exclude_when_contains):
                    continue
                # Déclenchement : OR entre trigger_contains et trigger_regex.
                _found = [t for t in _triggers if t in _fc]
                for _rx_src, _rx in _compiled_regexes:
                    if _rx.search(_fc):
                        _found.append(f"regex:{_rx_src}")
                _has_explicit_triggers = bool(_triggers or _compiled_regexes)
                if _has_explicit_triggers and not _found:
                    continue
                if not _has_explicit_triggers:
                    _found = ["scope"]

                _missing_constraints = []
                for _needle in _requires_contains_all:
                    if _needle not in _fc:
                        _missing_constraints.append(f"contains:{_needle}")
                for _rx_src, _rx in _compiled_required_regexes:
                    if not _rx.search(_fc):
                        _missing_constraints.append(f"regex:{_rx_src}")
                if _missing_constraints:
                    _violations.append((_fp_norm, _found + [f"missing:{c}" for c in _missing_constraints]))
                    continue
                # Si une directive est requise, vérifier la première ligne non-vide
                # Normalisation : on retire les guillemets et le ';' terminal pour comparer
                # le contenu sémantique ('use client', "use client", 'use client'; → même chose)
                if _directive is not None or _conflicts is not None:
                    _first = _first_directive_line(
                        _fc, ignore_leading_comments=_ignore_leading_comments
                    )
                    _first_norm = _first.replace("'", "").replace('"', "").rstrip(";").strip()
                    if _directive is not None and _directive in _first_norm:
                        continue  # directive requise présente — pas de violation
                    if _conflicts is not None and _conflicts not in _first_norm:
                        continue  # directive conflictuelle absente — pas de violation
                _violations.append((_fp_norm, _found))

            if _violations:
                _details = "\n".join(
                    f"  - {fp}  [{', '.join(found)}]"
                    for fp, found in _violations
                )
                _msg = "\n".join(_msg_lines).replace("{details}", _details)
                if _mode == "warn":
                    _guard_warning_hits[_gid] = _guard_warning_hits.get(_gid, 0) + len(_violations)
                    logger.warning(f"[CONTENT_GUARD WARN {_gid}] {len(_violations)} violation(s) — non bloquant")
                    _warnings.append(f"[CONTENT_GUARD WARNING:{_gid}]\n{_msg}")
                    continue
                return True, _msg, _gid, _warnings

        return False, "", "", _warnings

    def _requirements_gate(reqs: list, files_dict: dict) -> tuple:
        """
        Gate déterministe : vérifie que les requirements métier mappables sont couverts.
        Délègue à requirements_engine.gate_check — source de vérité unique (T002).
        Retourne (bloqué: bool, message: str).
        """
        blocked, msg = _engine_gate_check(reqs, files_dict)
        if not blocked:
            return False, msg
        return blocked, msg

    def _missing_required_files(required_paths: list[str], files_dict: dict) -> list[str]:
        if not required_paths:
            return []
        present_paths = {k.replace("\\", "/").lower() for k in files_dict.keys()}
        missing: list[str] = []
        for p in required_paths:
            p_norm = str(p).replace("\\", "/").lower()
            if not any(pp == p_norm or pp.endswith("/" + p_norm) for pp in present_paths):
                missing.append(p)
        return _sort_paths_by_priority(missing)

    def _sort_requirements_by_priority(reqs: list[str]) -> list[str]:
        if not reqs:
            return []
        decorated: list[tuple[int, str, str]] = []
        for req in reqs:
            _primary = _extract_primary_path_from_requirement(req)
            decorated.append((_path_priority_rank(_primary), _primary, req))
        decorated.sort(key=lambda t: (t[0], t[1].lower(), t[2].lower()))
        return [t[2] for t in decorated]

    def _collect_blocking_content_guard_targets(files_dict: dict) -> tuple[str, list[str]]:
        """
        Retourne (guard_id, paths) du premier content_guard bloquant en violation.
        Sans side-effects: aucune écriture de message dans l'historique.
        """
        for guard in stack_cfg.get("content_guards", []):
            gid = str(guard.get("id", "unknown"))
            mode = str(guard.get("mode", "block")).strip().lower()
            if mode not in ("block", "warn"):
                mode = "block"
            if mode != "block":
                continue

            file_prefix = str(guard.get("file_prefix", ""))
            file_exts = guard.get("file_extensions", []) or []
            triggers = guard.get("trigger_contains", []) or []
            trigger_regexes = guard.get("trigger_regex", []) or []
            requires_contains_all = guard.get("requires_contains_all", []) or []
            requires_regex_all = guard.get("requires_regex_all", []) or []
            directive = guard.get("requires_first_directive")
            conflicts = guard.get("conflicts_with_directive")
            exclude_paths = [str(p).replace("\\", "/") for p in (guard.get("exclude_paths", []) or [])]
            exclude_when_contains = [str(s) for s in (guard.get("exclude_when_contains", []) or [])]
            ignore_leading_comments = bool(guard.get("ignore_leading_comments", False))

            compiled_regexes: list[re.Pattern] = []
            for rx in trigger_regexes:
                try:
                    compiled_regexes.append(re.compile(str(rx), re.MULTILINE))
                except re.error:
                    continue
            compiled_required_regexes: list[re.Pattern] = []
            for rx in requires_regex_all:
                try:
                    compiled_required_regexes.append(re.compile(str(rx), re.MULTILINE))
                except re.error:
                    continue

            violating_paths: list[str] = []
            for fp, fc in files_dict.items():
                fp_norm = fp.replace("\\", "/")
                if fp_norm in _templated_names:
                    continue
                if any(fp_norm.startswith(xp) for xp in exclude_paths):
                    continue
                if file_prefix and not fp_norm.startswith(file_prefix):
                    continue
                if file_exts and not any(fp_norm.endswith(ext) for ext in file_exts):
                    continue
                if exclude_when_contains and any(needle in fc for needle in exclude_when_contains):
                    continue

                found = any(t in fc for t in triggers)
                if not found and compiled_regexes:
                    found = any(rx.search(fc) for rx in compiled_regexes)
                has_explicit_triggers = bool(triggers or compiled_regexes)
                if has_explicit_triggers and not found:
                    continue

                if any(needle not in fc for needle in requires_contains_all):
                    violating_paths.append(fp_norm)
                    continue
                if any(not rx.search(fc) for rx in compiled_required_regexes):
                    violating_paths.append(fp_norm)
                    continue

                if directive is not None or conflicts is not None:
                    first = _first_directive_line(fc, ignore_leading_comments=ignore_leading_comments)
                    first_norm = first.replace("'", "").replace('"', "").rstrip(";").strip()
                    if directive is not None and directive in first_norm:
                        continue
                    if conflicts is not None and conflicts not in first_norm:
                        continue

                violating_paths.append(fp_norm)

            if violating_paths:
                return gid, violating_paths
        return "", []

    def _build_run_state(files_dict: dict) -> dict:
        cov = _engine_compute_coverage_detailed(requirements or [], files_dict)
        unmet = _sort_requirements_by_priority(cov.get("unmet", []))
        missing_files = _missing_required_files(llm_required_files, files_dict)
        structural_gid, structural_paths = _collect_blocking_content_guard_targets(files_dict)
        # Priorité convergence: créer d'abord les fichiers blueprint manquants.
        # Sinon l'agent peut boucler sur des détails requirements sans jamais
        # produire le fichier racine attendu par le gate structural.
        if missing_files:
            blocker = f"file_missing::{missing_files[0]}"
        elif structural_gid:
            blocker = f"structural::{structural_gid}"
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

    def _extract_primary_path_from_requirement(req: str) -> str:
        req = req or ""
        req_lower = req.lower()
        route_match = re.search(r'(GET|POST|PUT|PATCH|DELETE)\s+(/[\w/\[\]-]+)', req, re.IGNORECASE)
        if route_match:
            return f"app/{route_match.group(2).strip('/')}/route.ts"
        if "page" in req_lower:
            page_match = re.search(r'/[\w\[\]/\-]+', req)
            if page_match:
                return f"app/{page_match.group(0).strip('/')}/page.tsx"
            if re.search(r'(^|[\s:(])/(?=$|[\s),.:;])', req):
                return "app/page.tsx"
        if "modèle prisma" in req_lower or "model prisma" in req_lower or "prisma:" in req_lower:
            return "prisma/schema.prisma"
        return ""

    def _allowed_paths_for_blocker(state: dict) -> list[str]:
        blocker = state.get("active_blocker", "")
        if blocker.startswith("file_missing::"):
            p = blocker.split("::", 1)[1].strip()
            allowed = [p] if p else []
            # scaffold_extends files (ex: prisma/schema.prisma) doivent toujours être
            # autorisés : le LLM doit pouvoir les écrire quel que soit le blocker actif.
            allowed.extend(scaffold_extends_paths)
            return allowed
        if blocker.startswith("requirements::"):
            req = blocker.split("::", 1)[1]
            primary = _extract_primary_path_from_requirement(req)
            allowed: list[str] = []
            if primary:
                allowed.append(primary)
            req_lower = req.lower()
            if "modèle prisma" in req_lower or "model prisma" in req_lower or "prisma:" in req_lower:
                allowed.extend(["prisma/schema.prisma", "lib/prisma.ts", "prisma.config.ts"])
            return allowed
        if blocker.startswith("structural::"):
            targets = state.get("structural_targets", []) or []
            allowed = [str(t).replace("\\", "/") for t in targets]
            allowed.extend(scaffold_extends_paths)
            return allowed
        return []

    def _path_is_allowed_for_objective(path: str, allowed_paths: list[str], blocker: str = "") -> bool:
        if not allowed_paths:
            return True
        p = (path or "").replace("\\", "/").strip()
        p_lower = p.lower()
        # scaffold_extends files (ex: prisma/schema.prisma) sont toujours autorisés quel
        # que soit le blocker actif : ce sont des fichiers fondamentaux à étendre par le LLM.
        if p_lower in {s.replace("\\", "/").lower() for s in scaffold_extends_paths}:
            return True
        # Si le blocker exige un fichier précis, ne pas autoriser d'écritures latérales.
        if blocker.startswith("file_missing::"):
            return any(p_lower == a.replace("\\", "/").lower() for a in allowed_paths)
        if blocker.startswith("structural::"):
            return any(p_lower == a.replace("\\", "/").lower() for a in allowed_paths)
        commons = {
            "package.json",
            ".env.local",
            "next.config.js",
            "tsconfig.json",
            "app/layout.tsx",
            "middleware.ts",
        }
        if p_lower in commons:
            return True
        allowed_norm = [a.replace("\\", "/").lower() for a in allowed_paths]
        return any(p_lower == a or p_lower.startswith(a.rsplit("/", 1)[0] + "/") for a in allowed_norm)

    progress_summary = {
        "what_done": [],
        "what_missing": [],
        "next_action": "Démarrer par l'objectif actif",
    }

    def _update_progress_summary(state: dict) -> None:
        unmet = state.get("requirements_unmet", [])
        missing_files = state.get("missing_required_files", [])
        met = state.get("requirements_met", 0)
        total = state.get("requirements_total", 0)
        done = [f"requirements_couverts={met}/{total}"]
        if not unmet:
            done.append("requirements_mappables_couverts")
        progress_summary["what_done"] = done
        missing = []
        if unmet:
            missing.append(f"requirement: {unmet[0]}")
        if missing_files:
            missing.append(f"fichier: {missing_files[0]}")
        if state.get("last_build_error_excerpt"):
            missing.append("corriger dernière erreur build")
        progress_summary["what_missing"] = missing or ["aucun blocage détecté"]
        progress_summary["next_action"] = (
            "appeler run_build"
            if state.get("active_blocker") == "ready_for_build"
            else f"corriger {state.get('active_blocker')}"
        )

    def _build_progress_summary_text() -> str:
        return (
            "SUMMARY LOOP:\n"
            f"- DONE: {' | '.join(progress_summary['what_done'])}\n"
            f"- MISSING: {' | '.join(progress_summary['what_missing'])}\n"
            f"- NEXT: {progress_summary['next_action']}"
        )

    def _build_iteration_brief(state: dict) -> str:
        unmet = state.get("requirements_unmet", [])
        missing_files = state.get("missing_required_files", [])
        objective = state.get("active_blocker", "ready_for_build")
        statuses = state.get("requirements_statuses", [])
        first_unmet_reason = ""
        for s in statuses:
            if s.get("is_mappable") and not s.get("satisfied"):
                first_unmet_reason = s.get("reason", "")
                break
        lines = [
            "FOCUS LOOP (itération courante) — travaille sur UNE priorité à la fois.",
            f"OBJECTIF UNIQUE: {objective}",
            f"REQUIREMENTS: {state.get('requirements_met', 0)}/{state.get('requirements_total', 0)} couverts",
        ]
        if unmet:
            lines.append("REQUIREMENT PRIORITAIRE NON COUVERT:")
            lines.append(f"- {unmet[0]}")
            if first_unmet_reason:
                lines.append(f"- DÉTAIL: {first_unmet_reason}")
        if missing_files:
            lines.append("FICHIER REQUIS PRIORITAIRE MANQUANT:")
            lines.append(f"- {missing_files[0]}")
        if objective.startswith("structural::"):
            guard_id = state.get("structural_blocking_guard_id", "")
            targets = state.get("structural_targets", []) or []
            lines.append(f"GUARD STRUCTUREL BLOQUANT: {guard_id}")
            if targets:
                lines.append("FICHIERS À CORRIGER (OBLIGATOIRE avant tout autre écriture):")
                for p in targets[:3]:
                    lines.append(f"- {p}")
            # Inject guard message_lines so the LLM knows exactly what to fix
            guard_cfg = next(
                (g for g in stack_cfg.get("content_guards", []) if g.get("id") == guard_id),
                None,
            )
            if guard_cfg:
                msg_lines = guard_cfg.get("message_lines", [])
                if msg_lines:
                    lines.append("INSTRUCTIONS DE CORRECTION:")
                    for ml in msg_lines:
                        if ml == "{details}":
                            for p in targets[:3]:
                                lines.append(f"  - {p}")
                        else:
                            lines.append(ml)
        err = state.get("last_build_error_excerpt", "")
        if err:
            lines.append("DERNIÈRE ERREUR BUILD (extrait):")
            lines.append(err)
        lines.append(
            "ACTION: corrige les fichiers listés ci-dessus en priorité absolue, puis valide par run_build."
        )
        lines.append(_build_progress_summary_text())
        return "\n".join(lines)

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
        main_messages = _main_context(messages, max_chars=_ctx_budget)
        run_state = _build_run_state(files)
        _update_progress_summary(run_state)
        main_messages.append(HumanMessage(content=_build_iteration_brief(run_state)))
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
                            _allowed = _allowed_paths_for_blocker(run_state)
                            _path = str(call_args.get("path", ""))
                            if not _path_is_allowed_for_objective(
                                _path, _allowed, run_state.get("active_blocker", "")
                            ):
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
                            computed_dir = _find_project_dir(files)
                            if computed_dir != "." and call_args.get("project_dir", ".") == ".":
                                call_args = {**call_args, "project_dir": computed_dir}
                                logger.info(f"[run_build] project_dir corrigé: '.' → '{computed_dir}'")
                            # ── PRE-BUILD GATES (Blueprint + UseState + Prisma) ──────────────
                            # T004 — transition d'état explicite
                            _prev_state = _state
                            _state = _SM_STRUCT_GATES
                            logger.info(f"[STATE] {_prev_state} → {_state}")
                            _gate_blocked, _gate_msg, _, _gate_warns = _prebuild_gates(files)
                            iter_gate_warnings.extend(_gate_warns)
                            if not _gate_blocked:
                                # ── REQUIREMENTS GATE ─────────────────────────────────────────
                                _prev_state = _state
                                _state = _SM_REQ_GATES
                                logger.info(f"[STATE] {_prev_state} → {_state}")
                                _gate_blocked, _gate_msg = _requirements_gate(requirements, files)
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

                        shrunk_output = _shrink_tool_output(tool_name, raw_output)
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
                        try:
                            workdir = os.getenv("FACTORY_WORKDIR", ".")
                            disk_path = os.path.normpath(os.path.join(workdir, path))
                            with open(disk_path, "r", encoding="utf-8") as _df:
                                files[path] = _df.read()
                        except Exception:
                            files[path] = content  # fallback si lecture échoue
                        wrote_file_this_iter = True
                        logger.info(f"Fichier généré : {path}")

        # Détection build succès/échec déterministe: uniquement depuis run_build.
        if build_failed_this_iter:
            build_attempts += 1

        if wrote_file_this_iter or called_build_this_iter:
            stagnant_iterations = 0
        else:
            stagnant_iterations += 1

        # Vérification immédiate du blocker actif après écriture.
        if wrote_file_this_iter:
            _post_write_state = _build_run_state(files)
            _pre_blocker = run_state.get("active_blocker", "")
            _post_blocker = _post_write_state.get("active_blocker", "")
            if _pre_blocker and _pre_blocker == _post_blocker and _pre_blocker != "ready_for_build":
                _allowed = _allowed_paths_for_blocker(_post_write_state)
                _allowed_msg = ", ".join(_allowed) if _allowed else "aucune restriction"
                messages.append(HumanMessage(content=(
                    "[IMMEDIATE_VERIFY] Le blocker actif n'a pas été résolu dans ce tour.\n"
                    f"Blocker courant: {_post_blocker}\n"
                    f"Chemins autorisés maintenant: {_allowed_msg}\n"
                    "Corrige ce blocker en priorité avant toute autre écriture."
                )))

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
                messages.append(HumanMessage(content=(
                    f"⚠️ ERREUR DE SÉQUENCE CRITIQUE : Tu as écrit {non_pkg_files} avant {_primary}.\n"
                    f"RÈGLE ABSOLUE : {_primary} DOIT être le PREMIER fichier généré, AVANT TOUT AUTRE.\n"
                    f"ACTION OBLIGATOIRE IMMÉDIATE : génère {_primary} maintenant avec les versions exactes :\n"
                    + "\n".join(f'  "{pkg}": "{ver}"' for pkg, ver in packages.items())
                    + f"\n\nNe génère AUCUN autre fichier avant que {_primary} soit écrit."
                )))

        # Forçage progression si fichiers clés présents
        _pdir = _find_project_dir(files)  # Hard rule: répertoire réel du projet
        if all(any(k in p for p in files) for k in key_files) and not build_success:
            # Ordre: d'abord les gates structurelles (_prebuild_gates), puis requirements.
            # Garantit que le LLM reçoit le feedback le plus proche du blocage réel.
            _early_gates_blocked, _early_gates_msg, _, _early_gate_warns = _prebuild_gates(files)
            iter_gate_warnings.extend(_early_gate_warns)
            if _early_gates_blocked:
                messages.append(HumanMessage(content=f"[PRE_BUILD_CHECK]\n{_early_gates_msg}"))
            else:
                _rg_early_blocked, _rg_early_msg = _requirements_gate(requirements, files)
                if _rg_early_blocked:
                    messages.append(HumanMessage(content=f"[REQUIREMENTS CHECK]\n{_rg_early_msg}"))
                else:
                    messages.append(HumanMessage(content=f"Fichiers clés présents. Appelle run_build(project_dir='{_pdir}') maintenant pour valider le projet."))

        # Garde-fou: si le modele stagne sans progres, forcer un run_build.
        if not build_success and not called_build_this_iter and (stagnant_iterations >= 2 or iteration >= MAX_ITERATIONS - 1):
            # ── Même gates pré-build que le chemin tool_call ──────────────────
            _forced_blocked, _forced_msg, _, _forced_gate_warns = _prebuild_gates(files)
            iter_gate_warnings.extend(_forced_gate_warns)
            if not _forced_blocked:
                _forced_blocked, _forced_msg = _requirements_gate(requirements, files)
            if _forced_blocked:
                messages.append(HumanMessage(content=f"[PRE_BUILD_CHECK]\n{_forced_msg}"))
                logger.warning(f"[PreBuildGate] FORCED BUILD BLOQUÉ — fichiers manquants ou violations")
                stagnant_iterations = 0  # reset pour laisser l'agent corriger
            else:
                forced_build_output = str(run_build.invoke({"project_dir": _pdir}))
                build_attempted = True
                called_build_this_iter = True
                raw_tool_outputs.append(forced_build_output)
                messages.append(HumanMessage(content=f"[FORCED_RUN_BUILD]\n{_shrink_tool_output('run_build', forced_build_output)}"))
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

        messages.append(HumanMessage(content=reflection))
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
        _tg_dir = _find_project_dir(files)
        _tg_blocked, _tg_msg, _tg_gid, _ = _prebuild_gates(files)
        _tg_is_structural = _tg_blocked
        if not _tg_blocked:
            _tg_blocked, _tg_msg = _requirements_gate(requirements, files)
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
    _rel_dir = _find_project_dir(files)
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
    return {
        "files": files,
        "final_message": final_message,
        "success": build_success,
        "metadata": {
            "iterations": iteration,
            "build_attempts": build_attempts,
            "build_attempted": build_attempted,
            "total_files": len(files),
            "last_build_error": last_build_error[:2000] if last_build_error else "",
            "last_build_error_full": last_build_error_full if last_build_error_full else "",
            "last_test_error": last_test_error[:2000] if last_test_error else "",
            "last_test_error_full": last_test_error_full if last_test_error_full else "",
            "last_failed_command": last_failed_command,
            "gate_source": _final_gate_source,
            "blocking_guard_id": _final_blocking_guard_id,
            "gate_message": _final_gate_message,
            "missing_required_files": _final_missing_required_files,
            "guard_warning_hits": _guard_warning_hits,
            "guard_warning_count": sum(_guard_warning_hits.values()),
        },
    }

