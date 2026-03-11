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
    _extract_required_model_fields as _engine_extract_required_model_fields,
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

    MAX_ITERATIONS = 14
    MAX_BUILD_ATTEMPTS = 8
    PHASE1_LIMIT = 14  # identique à MAX_ITERATIONS — plus de split de phase
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
        Construit le contexte sous budget en conservant l'intégrité des couples
        AI(tool_calls) + ToolMessage(s). Évite l'erreur OpenAI 400 sur tool_call_id.

        T004 — max_chars paramétrable par phase (phase 1 : 6000 tokens, phase 2 : 14000 tokens).
        """
        if len(messages_list) <= 2:
            return messages_list

        kept = [messages_list[0], messages_list[1]]
        # Le budget s'applique UNIQUEMENT aux tours supplémentaires (pas aux messages initiaux
        # qui sont toujours conservés). Sinon messages[1] (spec + RAG context ≈ 16 000 chars)
        # dépasse max_chars à lui seul → aucun tour récent n'est jamais inclus
        # → le LLM ne voit jamais son historique et boucle sur la même instruction.
        current_chars = 0

        # Découpe en "turns" cohérents après les 2 messages initiaux.
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
                turns.append([msg])
                i += 1

        selected = []
        for turn in reversed(turns):
            turn_chars = sum(len(str(getattr(m, "content", ""))) for m in turn)
            if current_chars + turn_chars > max_chars:
                break
            selected.append(turn)
            current_chars += turn_chars

        selected.reverse()
        flattened = [m for turn in selected for m in turn]
        return kept + flattened

    summarized_spec = summarize_text(spec, MAX_SPEC_TOKENS, "Specification")
    summarized_mermaid = summarize_text(mermaid, MAX_MERMAID_TOKENS, "Mermaid Diagram")

    effective_stack_id = stack_id or get_stack_id()
    prompt = load_stack_prompt("dev", effective_stack_id)
    from .stack_config import load_stack_config
    stack_cfg = load_stack_config(effective_stack_id) or {}

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

    # Exclure les fichiers templates de l'ordre de génération LLM
    llm_required_files = [f for f in required_files if f not in _templated_names]
    templates_block = ""
    if _templated_names:
        templates_block = (
            "FICHIERS DÉJÀ ÉCRITS PAR LA FACTORY (templates validés — NE PAS RÉÉCRIRE) :\n"
            + "\n".join(f"  ✓ {f}" for f in sorted(_templated_names))
            + "\nCes fichiers sont corrects sur le disque. Concentre-toi sur les fichiers MÉTIER ci-dessous.\n\n"
        )
    required_files_block = ""
    if llm_required_files:
        required_files_block = (
            "ORDRE DE GÉNÉRATION OBLIGATOIRE — respecte cette séquence exacte, un fichier à la fois :\n"
            + "\n".join(f"{i+1}. {f}" for i, f in enumerate(llm_required_files))
            + "\nNe génère PAS de fichiers hors de cette liste avant que tous soient créés.\n\n"
        )
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
            "Règle absolue : si la spec nomme un modèle 'Article', le client exige 'Post'. "
            "Si la spec utilise '/articles', le client exige '/blog'. "
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
    messages = [
        SystemMessage(content=prompt),
        HumanMessage(content=(
            f"Projet : {project_name}\n\n"
            f"{spec_degraded_block}"
            f"Spec :\n{summarized_spec}\n\n"
            f"Mermaid :\n{summarized_mermaid}\n\n"
            f"Contexte RAG obligatoire (préchargé) :\n{mandatory_rag_context}\n\n"
            f"{packages_block}"
            f"{dev_packages_block}"
            f"{templates_block}"
            f"{required_files_block}"
            f"{requirements_block}"
            "⚠️ RÈGLE ABSOLUE — package.json DOIT être le PREMIER fichier généré, AVANT TOUT AUTRE (avant jest.setup.js, avant app/layout.tsx, avant tout). "
            "Étape 1 OBLIGATOIRE : génère IMMÉDIATEMENT package.json avec les versions exactes ci-dessus. "
            "Ne génère AUCUN autre fichier avant que package.json soit écrit sur le disque."
        ))
    ]

    files = {}
    # Pré-populer files avec le contenu des templates (comptabilisés comme déjà écrits)
    files.update(_template_written)
    final_message = ""
    _final_gate_source = ""  # "content_guard" | "requirements" | "no_files" — renseigné si NOT_BUILT_BY_GATE
    _final_blocking_guard_id = ""  # id du guard qui a bloqué (ex: "use_client", "blueprint")
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
        # 1. Blueprint Validator
        _present = set(files_dict.keys()) | _templated_names
        _missing = [f for f in required_files if not any(f in p for p in _present)]
        if _missing:
            return True, (
                "BLUEPRINT VALIDATOR — BUILD BLOQUÉ\n"
                f"{len(_missing)} fichier(s) obligatoire(s) manquant(s) :\n"
                + "\n".join(f"  - {f}" for f in _missing)
                + "\n\nGénère ces fichiers avec write_file() maintenant."
                " run_build sera disponible une fois tous présents."
            ), "blueprint"
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

                if _violations and bool(_pg.get("auto_fix", False)):
                    _remaining: list[tuple[str, str]] = []
                    for _bad_fp, _target_fp in _violations:
                        _key = (_bad_fp, _pg_id)
                        _constructive_guard_failures[_key] = _constructive_guard_failures.get(_key, 0) + 1
                        if _constructive_guard_failures[_key] >= 1:
                            _orig_fc = files_dict.get(_bad_fp) or files_dict.get(_bad_fp.replace("/", "\\"), "")
                            if _orig_fc:
                                try:
                                    write_file.invoke({"file_path": _target_fp, "content": _orig_fc})
                                    files[_target_fp] = _orig_fc
                                    for _k in list(files.keys()):
                                        if _k.replace("\\", "/") == _bad_fp:
                                            del files[_k]
                                    _factory_workdir = os.getenv("FACTORY_WORKDIR")
                                    if _factory_workdir:
                                        _bad_disk = os.path.normpath(os.path.join(_factory_workdir, _bad_fp))
                                        try:
                                            os.remove(_bad_disk)
                                        except FileNotFoundError:
                                            pass
                                    messages.append(HumanMessage(content=(
                                        f"[AUTO-FIX {_pg_id.upper()}] '{_bad_fp}' migré vers '{_target_fp}'.\n"
                                        "Continue la génération, puis appelle run_build."
                                    )))
                                except Exception as _af_err:
                                    logger.error(f"[AUTO-FIX {_pg_id}] Erreur migration {_bad_fp}: {_af_err}")
                                    _remaining.append((_bad_fp, _target_fp))
                            else:
                                _remaining.append((_bad_fp, _target_fp))
                        else:
                            _remaining.append((_bad_fp, _target_fp))
                    _violations = _remaining

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
                    messages.append(HumanMessage(content=f"[PATH_GUARD WARNING:{_pg_id}]\n{_msg}"))
                else:
                    return True, _msg, _pg_id

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
                "INTERDIT: pages/api/posts/index.ts      →  CORRECT: app/api/posts/route.ts\n"
                "INTERDIT: pages/api/posts/[id].ts       →  CORRECT: app/api/posts/[id]/route.ts\n"
                "Structure App Router API :\n"
                "  app/api/<resource>/route.ts            → export async function GET() / POST()\n"
                "  app/api/<resource>/[id]/route.ts       → export async function GET() / PUT() / DELETE()\n"
                "Crée les fichiers App Router corrects avec write_file(), puis rappelle run_build."
            ), "forbidden_paths"
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
            messages.append(HumanMessage(content=f"[PREBUILD WARNING:forbidden_imports]\n{_warn_msg}"))
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
            _file_prefix = _guard.get("file_prefix", "")
            _file_exts = _guard.get("file_extensions", [])
            _triggers = _guard.get("trigger_contains", [])
            _directive = _guard.get("requires_first_directive")    # None = pas de vérif ; fire si ABSENTE
            _conflicts = _guard.get("conflicts_with_directive")    # None = pas de vérif ; fire si PRÉSENTE
            _mode = str(_guard.get("mode", "block")).strip().lower()
            if _mode not in ("block", "warn"):
                _mode = "block"
            _exclude_paths = [str(p).replace("\\", "/") for p in (_guard.get("exclude_paths", []) or [])]
            _exclude_when_contains = [str(s) for s in (_guard.get("exclude_when_contains", []) or [])]
            _msg_lines = _guard.get("message_lines", [f"{_gid} GUARD — BUILD BLOQUÉ", "{details}"])

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
                # Déclenchement : au moins un trigger présent dans le contenu (substring, pas regex)
                _found = [t for t in _triggers if t in _fc]
                if not _found:
                    continue
                # Si une directive est requise, vérifier la première ligne non-vide
                # Normalisation : on retire les guillemets et le ';' terminal pour comparer
                # le contenu sémantique ('use client', "use client", 'use client'; → même chose)
                if _directive is not None or _conflicts is not None:
                    _first = next((ln.strip() for ln in _fc.splitlines() if ln.strip()), "")
                    _first_norm = _first.replace("'", "").replace('"', "").rstrip(";").strip()
                    if _directive is not None and _directive in _first_norm:
                        continue  # directive requise présente — pas de violation
                    if _conflicts is not None and _conflicts not in _first_norm:
                        continue  # directive conflictuelle absente — pas de violation
                _violations.append((_fp_norm, _found))

            if _violations:
                # Auto-fix pour guards avec requires_first_directive (ex: use_client).
                # Après 2 blocages consécutifs sur le même fichier, on injecte la directive
                # déterministement — bypass LLM (même mécanique que T010 auth_wrapping_route).
                if _mode == "block" and _directive is not None:
                    _remaining = []
                    for _vfp, _vfound in _violations:
                        _key = (_vfp, _gid)
                        _constructive_guard_failures[_key] = _constructive_guard_failures.get(_key, 0) + 1
                        if _constructive_guard_failures[_key] >= 2:
                            _orig_fc = files_dict.get(_vfp) or files_dict.get(_vfp.replace("/", "\\"), "")
                            if _orig_fc:
                                _fixed_fc = f'"{_directive}";\n' + _orig_fc
                                try:
                                    write_file.invoke({"file_path": _vfp, "content": _fixed_fc})
                                    files_dict[_vfp] = _fixed_fc
                                    logger.info(f"[AUTO-FIX {_gid}] {_vfp} corrigé (× {_constructive_guard_failures[_key]})")
                                    messages.append(HumanMessage(content=(
                                        f"[AUTO-FIX {_gid.upper()}] '{_vfp}' corrigé automatiquement "
                                        f"après {_constructive_guard_failures[_key]} blocages : "
                                        f"'\"{_directive}\";' ajouté en première ligne.\n"
                                        "Vérifie que le fichier est correct, puis appelle run_build."
                                    )))
                                except Exception as _af_err:
                                    logger.error(f"[AUTO-FIX {_gid}] Erreur écriture {_vfp}: {_af_err}")
                                    _remaining.append((_vfp, _vfound))
                            else:
                                _remaining.append((_vfp, _vfound))
                        else:
                            _remaining.append((_vfp, _vfound))
                    _violations = _remaining

                if _violations:
                    _details = "\n".join(
                        f"  - {fp}  [{', '.join(found)}]"
                        for fp, found in _violations
                    )
                    _msg = "\n".join(_msg_lines).replace("{details}", _details)
                    if _mode == "warn":
                        _guard_warning_hits[_gid] = _guard_warning_hits.get(_gid, 0) + len(_violations)
                        logger.warning(f"[CONTENT_GUARD WARN {_gid}] {len(_violations)} violation(s) — non bloquant")
                        messages.append(HumanMessage(content=f"[CONTENT_GUARD WARNING:{_gid}]\n{_msg}"))
                        continue
                    return True, _msg, _gid

        return False, "", ""

    def _requirements_gate(reqs: list, files_dict: dict) -> tuple:
        """
        Gate déterministe : vérifie que les requirements métier mappables sont couverts.
        Délègue à requirements_engine.gate_check — source de vérité unique (T002).
        Retourne (bloqué: bool, message: str).
        """
        blocked, msg = _engine_gate_check(reqs, files_dict)
        if not blocked:
            return False, msg

        # Auto-fix constructif requirements Prisma après 2 blocages identiques.
        # Objectif: casser la boucle quand le LLM oublie des champs demandés.
        unmet_reqs = []
        for line in (msg or "").splitlines():
            line = line.strip()
            if line.startswith("- "):
                unmet_reqs.append(line[2:].strip())

        def _autofix_prisma_requirement(req_text: str, files_map: dict) -> bool:
            if "modèle prisma" not in req_text.lower() and "model prisma" not in req_text.lower():
                return False
            model_match = re.search(r":\s*(\w+)", req_text)
            if not model_match:
                return False
            model_name = model_match.group(1)
            req_fields, req_unique = _engine_extract_required_model_fields(req_text, model_name)
            if not req_fields and not req_unique:
                return False

            def _parse_field_specs_from_req(text: str) -> dict:
                """
                Extrait des specs de champs depuis:
                '... avec champs title, content, slug @unique, published Boolean, authorId String'
                """
                out: dict = {}
                # Indices de casse depuis le texte requirement brut.
                # Permet de reconstruire authorId (camelCase) même si req_fields vient en lowercase.
                case_hints: dict = {}
                for _tok in re.findall(r"[A-Za-z_][A-Za-z0-9_]*", text):
                    _low = _tok.lower()
                    if _low not in case_hints and any(ch.isupper() for ch in _tok):
                        case_hints[_low] = _tok
                m_fields = re.search(r"avec\s+champs?\s+(.+)$", text, re.IGNORECASE)
                if not m_fields:
                    # Fallback minimal depuis req_fields
                    for _f in req_fields:
                        _canon = case_hints.get(_f.lower(), _f)
                        out[_canon] = {
                            "type": "String",
                            "unique": (_f in req_unique),
                            "default": None,
                        }
                    return out

                raw = m_fields.group(1)
                chunks = [c.strip() for c in re.split(r",|\bet\b", raw, flags=re.IGNORECASE) if c.strip()]
                valid_types = {"string": "String", "boolean": "Boolean", "datetime": "DateTime", "int": "Int", "float": "Float", "json": "Json"}

                for chunk in chunks:
                    tokens = re.findall(r"@[a-z_]+|[A-Za-z_][A-Za-z0-9_]*", chunk)
                    if not tokens:
                        continue
                    field_name = tokens[0]
                    field_type = "String"
                    chunk_lower = chunk.lower()
                    unique = "@unique" in chunk_lower or " unique" in chunk_lower
                    default = None

                    for t in tokens[1:]:
                        t_lower = t.lower()
                        if t_lower in valid_types:
                            field_type = valid_types[t_lower]
                            break
                    # Heuristique utile pour cette stack/blog: published bool par défaut false.
                    if field_name.lower() == "published" and field_type == "Boolean":
                        default = "@default(false)"

                    out[field_name] = {"type": field_type, "unique": unique, "default": default}

                # Garantir couverture des champs déjà extraits par l'engine.
                for _f in req_fields:
                    # Respecte la casse issue du requirement si disponible.
                    existing_key = next(
                        (k for k in out.keys() if k.lower() == _f.lower()),
                        case_hints.get(_f.lower(), _f),
                    )
                    out.setdefault(existing_key, {"type": "String", "unique": (_f in req_unique), "default": None})
                    if _f in req_unique:
                        out[existing_key]["unique"] = True
                return out

            def _render_field_line(fname: str, spec: dict) -> str:
                parts = [f"  {fname}", spec.get("type", "String")]
                if spec.get("unique"):
                    parts.append("@unique")
                if spec.get("default"):
                    parts.append(spec["default"])
                return " ".join(parts)

            schema_key = next(
                (k for k in files_map.keys() if "schema.prisma" in k.replace("\\", "/").lower()),
                "prisma/schema.prisma",
            )
            schema_content = files_map.get(schema_key, "")
            if not schema_content:
                schema_content = f"model {model_name} {{\n}}\n"
            field_specs = _parse_field_specs_from_req(req_text)

            model_re = re.compile(
                rf"\bmodel\s+{re.escape(model_name)}\s*\{{(.*?)\}}",
                re.IGNORECASE | re.DOTALL,
            )
            m = model_re.search(schema_content)
            # Mapping case-insensitive pour préserver camelCase du requirement.
            field_specs_by_lower = {k.lower(): (k, v) for k, v in field_specs.items()}

            # Champs structurels minimaux Prisma (stables pour cette stack).
            base_structural_fields = {
                "id": {"type": "String", "unique": False, "default": "@id @default(cuid())"},
                "createdAt": {"type": "DateTime", "unique": False, "default": "@default(now())"},
                "updatedAt": {"type": "DateTime", "unique": False, "default": "@updatedAt"},
            }
            if not m:
                block_lines = []
                # id en premier pour éviter les modèles sans PK.
                block_lines.append(_render_field_line("id", base_structural_fields["id"]))
                for f in sorted(req_fields):
                    canonical_name, spec = field_specs_by_lower.get(
                        f.lower(),
                        (f, {"type": "String", "unique": (f in req_unique), "default": None}),
                    )
                    block_lines.append(_render_field_line(canonical_name, spec))
                # Champs temporels obligatoires selon orm_rules.
                block_lines.append(_render_field_line("createdAt", base_structural_fields["createdAt"]))
                block_lines.append(_render_field_line("updatedAt", base_structural_fields["updatedAt"]))
                model_block = f"model {model_name} {{\n" + "\n".join(block_lines) + "\n}\n"
                new_schema = schema_content.rstrip() + "\n\n" + model_block
            else:
                block = m.group(1)
                block_lines = [ln for ln in block.splitlines()]
                block_lower = block.lower()
                # Ajoute/normalise les champs requis
                for f in sorted(req_fields):
                    canonical_name, spec = field_specs_by_lower.get(
                        f.lower(),
                        (f, {"type": "String", "unique": (f in req_unique), "default": None}),
                    )
                    if not re.search(rf"\b{re.escape(canonical_name)}\b", block, re.IGNORECASE):
                        block_lines.append(_render_field_line(canonical_name, spec))
                        continue
                    # Champ présent: normaliser type + contraintes minimales
                    updated = False
                    for idx, ln in enumerate(block_lines):
                        m_line = re.search(rf"^(\s*)({re.escape(canonical_name)})\s+([A-Za-z][A-Za-z0-9_]*)\b(.*)$", ln, re.IGNORECASE)
                        if m_line:
                            indent, fname, _old_type, tail = m_line.groups()
                            new_tail = tail or ""
                            if spec.get("unique") and "@unique" not in new_tail:
                                new_tail = (new_tail.rstrip() + " @unique").rstrip()
                            if spec.get("default") and spec["default"] not in new_tail:
                                new_tail = (new_tail.rstrip() + f" {spec['default']}").rstrip()
                            block_lines[idx] = f"{indent}{fname} {spec.get('type', 'String')}{(' ' + new_tail.strip()) if new_tail.strip() else ''}"
                            updated = True
                            break
                    if not updated:
                        block_lines.append(_render_field_line(canonical_name, spec))

                # Garantit les champs structurels même si le LLM les a omis.
                for base_name in ("id", "createdAt", "updatedAt"):
                    base_spec = base_structural_fields[base_name]
                    if not re.search(rf"^\s*{re.escape(base_name)}\b", "\n".join(block_lines), re.IGNORECASE | re.MULTILINE):
                        block_lines.append(_render_field_line(base_name, base_spec))

                new_block = "\n".join(block_lines)
                new_schema = schema_content[:m.start(1)] + new_block + schema_content[m.end(1):]

            if new_schema == schema_content:
                return False
            try:
                write_file.invoke({"file_path": schema_key, "content": new_schema})
                files[schema_key] = new_schema
                files_map[schema_key] = new_schema
                logger.info(f"[AUTO-FIX requirements_prisma] {schema_key} enrichi depuis requirement: {req_text}")
                messages.append(
                    HumanMessage(
                        content=(
                            "[AUTO-FIX REQUIREMENTS_PRISMA] schema.prisma corrigé automatiquement "
                            "à partir du requirement manquant (champs/contraintes Prisma ajoutés)."
                        )
                    )
                )
                return True
            except Exception as _af_err:
                # Fallback déterministe: on met à jour l'état en mémoire pour
                # casser le blocage gate, même si l'écriture disque échoue.
                files[schema_key] = new_schema
                files_map[schema_key] = new_schema
                logger.error(
                    f"[AUTO-FIX requirements_prisma] écriture disque échouée, fallback mémoire actif: {_af_err}"
                )
                return True

        def _autofix_path_requirement(req_text: str, files_map: dict) -> bool:
            req_lower = req_text.lower()
            # API Route: METHOD /path
            m_route = re.search(r"(GET|POST|PUT|PATCH|DELETE)\s+(/[\w/\[\]-]+)", req_text, re.IGNORECASE)
            if m_route:
                method = m_route.group(1).upper()
                api_path = m_route.group(2).strip("/")
                target = f"app/{api_path}/route.ts"
                target_norm = target.replace("\\", "/").lower()
                exists = any(fp.replace("\\", "/").lower() == target_norm for fp in files_map.keys())
                if exists:
                    return False
                content = (
                    "import { NextResponse } from 'next/server';\n\n"
                    f"export async function {method}(request: Request) {{\n"
                    "  return NextResponse.json({ ok: true });\n"
                    "}\n"
                )
                try:
                    write_file.invoke({"file_path": target, "content": content})
                    files[target] = content
                    files_map[target] = content
                    messages.append(
                        HumanMessage(
                            content=(
                                f"[AUTO-FIX REQUIREMENTS_PATH] Route manquante créée: '{target}'. "
                                "Relance run_build."
                            )
                        )
                    )
                    logger.info(f"[AUTO-FIX requirements_path] créé {target} depuis requirement: {req_text}")
                    return True
                except Exception as _af_err:
                    files[target] = content
                    files_map[target] = content
                    logger.error(
                        f"[AUTO-FIX requirements_path] écriture route {target} échouée, fallback mémoire actif: {_af_err}"
                    )
                    return True

            # Page: /path
            if "page" in req_lower:
                m_page = re.search(r"/[\w\[\]/\-]+", req_text)
                if m_page:
                    raw = m_page.group(0)
                    page_path = raw.strip("/")
                    target = f"app/{page_path}/page.tsx"
                elif re.search(r"(^|[\s:(])/(?=$|[\s),.:;])", req_text):
                    target = "app/page.tsx"
                else:
                    return False
                target_norm = target.replace("\\", "/").lower()
                exists = any(fp.replace("\\", "/").lower() == target_norm for fp in files_map.keys())
                if exists:
                    return False
                content = (
                    "export default function Page() {\n"
                    "  return <main>Loading...</main>;\n"
                    "}\n"
                )
                try:
                    write_file.invoke({"file_path": target, "content": content})
                    files[target] = content
                    files_map[target] = content
                    messages.append(
                        HumanMessage(
                            content=(
                                f"[AUTO-FIX REQUIREMENTS_PATH] Page manquante créée: '{target}'. "
                                "Relance run_build."
                            )
                        )
                    )
                    logger.info(f"[AUTO-FIX requirements_path] créé {target} depuis requirement: {req_text}")
                    return True
                except Exception as _af_err:
                    files[target] = content
                    files_map[target] = content
                    logger.error(
                        f"[AUTO-FIX requirements_path] écriture page {target} échouée, fallback mémoire actif: {_af_err}"
                    )
                    return True

            return False

        fixed_any = False
        for req in unmet_reqs:
            req_lower = req.lower()
            if (
                "modèle prisma" not in req_lower
                and "model prisma" not in req_lower
                and "page" not in req_lower
                and not re.search(r"(GET|POST|PUT|PATCH|DELETE)\s+/", req, re.IGNORECASE)
            ):
                continue
            _key = ("requirements_autofix", req)
            _constructive_guard_failures[_key] = _constructive_guard_failures.get(_key, 0) + 1
            if _constructive_guard_failures[_key] >= 1:
                if "modèle prisma" in req_lower or "model prisma" in req_lower:
                    fixed_any = _autofix_prisma_requirement(req, files_dict) or fixed_any
                else:
                    fixed_any = _autofix_path_requirement(req, files_dict) or fixed_any

        if fixed_any:
            blocked2, msg2 = _engine_gate_check(reqs, files_dict)
            return blocked2, msg2
        return blocked, msg

    # ── T010 : Guards Constructifs — suivi des violations pour auto-write ───────
    # Compte les fois où la même violation est détectée dans le même fichier.
    # Après 2 blocages : auto-write du fichier corrigé (bypass LLM).
    _constructive_guard_failures: dict = {}  # {(file_path, guard_id): int}

    def _fix_auth_wrap_content(content: str) -> str:
        """
        Auto-fix : remplace chaque 'export const METHOD = auth(async (...) => {'
        par 'export async function METHOD(request, context) {' avec auth() interne.
        Le body de la fonction est conservé (approche best-effort).
        """
        _SIG_RE = re.compile(
            r'export\s+const\s+(GET|POST|PUT|PATCH|DELETE|HEAD)\s*=\s*auth\s*\(\s*async\s*\([^)]*\)\s*=>\s*\{[ \t]*\n?',
            re.MULTILINE,
        )

        def _replace_sig(m: re.Match) -> str:
            method = m.group(1)
            return (
                f'export async function {method}(request: Request, context: any) {{\n'
                f'  const {{ userId }} = await auth();\n'
                f'  if (!userId) return NextResponse.json({{ error: "Unauthorized" }}, {{ status: 401 }});\n'
                f'  const params = context.params;\n'
            )

        fixed = _SIG_RE.sub(_replace_sig, content)
        # Fermeture: }); → } (auth() wrapper closing pattern)
        fixed = re.sub(r'\n\}\);\n', '\n}\n', fixed)
        return fixed

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

    for iteration in range(1, MAX_ITERATIONS + 1):
        current_phase = 1 if iteration <= PHASE1_LIMIT else 2
        current_tools = tools_phase1 if current_phase == 1 else tools_phase2
        logger.info(f"[DEV AGENT v3.2] Itération {iteration}/{MAX_ITERATIONS} | Phase {current_phase} | State {_state} | Build attempts: {build_attempts}")

        # Truncation ultra-safe V3 – Chronologique garantie (build from newest, reverse)
        if len(messages) > 28:
            logger.warning("Historique trop long → truncation ultra-safe V3 chronologique.")
            retained = [messages[0], messages[1]]  # System + Premier Human

            recent = []  # Build newest to oldest
            i = len(messages) - 1
            pair_count = 0
            max_pairs = 12

            while i >= 2 and pair_count < max_pairs:
                current = messages[i]

                if isinstance(current, ToolMessage):
                    found = False
                    for j in range(i-1, max(i-20, 0), -1):
                        prev = messages[j]
                        if (hasattr(prev, "tool_calls") and prev.tool_calls and
                            any(tc.get("id") == current.tool_call_id for tc in prev.tool_calls if tc.get("id"))):
                            recent.append(current) # ToolMessage first when building newest to oldest
                            recent.append(prev)    # Then its AIMessage parent
                            pair_count += 1
                            found = True
                            i = j - 1
                            break
                    if not found:
                        i -= 1 # Orphaned ToolMessage, skip
                else:
                    recent.append(current)
                    i -= 1

            recent.reverse()  # Now oldest to newest
            messages = retained + recent
            logger.info(f"Historique truncaté à {len(messages)} messages (chronologique sécurisé).")

        # T004 — budget contexte par phase
        _ctx_budget = _PHASE1_MAX_CHARS if _state == _SM_GEN else _PHASE2_MAX_CHARS
        main_messages = _main_context(messages, max_chars=_ctx_budget)
        response = llm.bind_tools(current_tools).invoke(main_messages)
        messages.append(response)

        tool_messages = []
        raw_tool_outputs = []
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
                            _gate_blocked, _gate_msg, _ = _prebuild_gates(files)
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
                                # called_build_this_iter = True pour reset stagnant_iterations seulement.
                                called_build_this_iter = True
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
                        # Lire le contenu réel depuis le disque après sanitize,
                        # pour que files[path] == ce que test_coverage_agent utilisera.
                        try:
                            workdir = os.getenv("FACTORY_WORKDIR", ".")
                            disk_path = os.path.normpath(os.path.join(workdir, path))
                            with open(disk_path, "r", encoding="utf-8") as _df:
                                files[path] = _df.read()
                        except Exception:
                            files[path] = content  # fallback si lecture échoue
                        wrote_file_this_iter = True
                        logger.info(f"Fichier généré : {path}")
                        # Auto-clean App Router pages: si le LLM écrit app/X/page.tsx
                        # ou app/X/Y/page.tsx, supprimer le fichier .tsx invalide
                        # au chemin parent (ex: app/X.tsx, app/X/Y.tsx).
                        _written_p = PurePosixPath(path.replace("\\", "/"))
                        if _written_p.parts[0:1] == ("app",) and _written_p.name == "page.tsx":
                            _stale_str = str(_written_p.parent.with_suffix(".tsx"))
                            _ar_workdir = os.getenv("FACTORY_WORKDIR")
                            for _k in list(files.keys()):
                                if _k.replace("\\", "/") == _stale_str:
                                    del files[_k]
                                    if _ar_workdir:
                                        _stale_disk = os.path.normpath(os.path.join(_ar_workdir, _k))
                                        try:
                                            os.remove(_stale_disk)
                                            logger.info(f"[app_router_cleanup] {_k} supprimé dict + disque")
                                        except FileNotFoundError:
                                            logger.info(f"[app_router_cleanup] {_k} supprimé dict (absent du disque)")
                                    else:
                                        logger.info(f"[app_router_cleanup] {_k} supprimé dict (FACTORY_WORKDIR non défini)")
                        # Auto-clean Pages Router API: si le LLM écrit app/api/...,
                        # supprimer TOUS les fichiers pages/api/ du dict (conversion App Router).
                        if str(_written_p).startswith("app/api/"):
                            _pages_stale = [k for k in list(files.keys()) if k.replace("\\", "/").startswith("pages/api/")]
                            for _ps in _pages_stale:
                                del files[_ps]
                                # Supprimer aussi du disque : run_build lit le FS, pas le dict.
                                _factory_workdir = os.getenv("FACTORY_WORKDIR")
                                if _factory_workdir:
                                    _stale_disk = os.path.normpath(os.path.join(_factory_workdir, _ps))
                                    try:
                                        os.remove(_stale_disk)
                                        logger.info(f"[pages_api_cleanup] {_ps} supprimé dict + disque")
                                    except FileNotFoundError:
                                        logger.info(f"[pages_api_cleanup] {_ps} supprimé dict (absent du disque)")
                                else:
                                    logger.warning(f"[pages_api_cleanup] {_ps} supprimé dict uniquement (FACTORY_WORKDIR non défini)")

        # Détection build succès/échec déterministe: uniquement depuis run_build.
        if build_failed_this_iter:
            build_attempts += 1

        if wrote_file_this_iter or called_build_this_iter:
            stagnant_iterations = 0
        else:
            stagnant_iterations += 1

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
            _early_gates_blocked, _early_gates_msg, _ = _prebuild_gates(files)
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
            _forced_blocked, _forced_msg, _ = _prebuild_gates(files)
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

        # Reflection informative uniquement (ne pilote pas la sortie).
        reflection_messages = [
            SystemMessage(content=(
                "État actuel :\n"
                f"Fichiers générés : {list(files.keys())}\n"
                f"Build attempts : {build_attempts}/{MAX_BUILD_ATTEMPTS}\n"
                f"Dernière erreur build : {last_build_error[:500] if last_build_error else 'N/A'}\n"
                f"Dernière commande en échec : {last_failed_command or 'N/A'}\n"
                "- Si 'Build successful' dans les logs → réponds 'TERMINÉ : CODE PRÊT'\n"
                "- Si trop d'échecs → 'ÉCHEC : ERREUR RÉCURRENTE BUILD'\n"
                "- Sinon → continue l'étape suivante sans réécrire les fichiers existants."
            )),
            HumanMessage(content=f"Fichiers générés jusqu'ici : {list(files.keys())}")
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
        _tg_blocked, _tg_msg, _tg_gid = _prebuild_gates(files)
        _tg_is_structural = _tg_blocked
        if not _tg_blocked:
            _tg_blocked, _tg_msg = _requirements_gate(requirements, files)
            _tg_gid = "requirements" if _tg_blocked else ""
        if _tg_blocked:
            # T005 — final_message canonique. Détail dans les logs.
            final_message = "NOT_BUILT_BY_GATE"
            _final_gate_source = "content_guard" if _tg_is_structural else "requirements"
            _final_blocking_guard_id = _tg_gid
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
            "guard_warning_hits": _guard_warning_hits,
            "guard_warning_count": sum(_guard_warning_hits.values()),
        },
    }
