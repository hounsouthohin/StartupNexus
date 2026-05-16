# agents/dev_graph.py
"""
Dev Agent v4 — LangGraph natif + outils Python natifs (dev_tools.py).
Remplace dev.py + dev_loop.py pour la nouvelle base.

Phase 3 : structure de base LangGraph
Phase 4A : Build Doctor + system prompt de qualité
Phase 4B : expected_files checklist + anti-loop error signature
Phase 5 : outils Python natifs — MCP retiré du chemin critique
28 Mars 2026.
"""
from __future__ import annotations

import logging
import operator
import os
import shutil
import subprocess
from typing import TypedDict, List, Annotated

from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, AIMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition

from . import dev_tools as _dev_tools_module
from .dev_tools import write_file, read_file, list_directory, shell_exec, file_exists
from agents.web_search import web_search

logger = logging.getLogger(__name__)

MAX_BUILD_ATTEMPTS = 3
MAX_GENERATION_TURNS = 15
_BASE_WORKDIR = os.getenv("FACTORY_WORKDIR", "/app/generated-projects")


DEV_TOOLS = [write_file, read_file, list_directory, shell_exec, file_exists]


def _check_next_dir_on_disk() -> bool:
    """Indique si .next/ est présent — utilisé pour le logging uniquement, jamais pour décider du succès."""
    return os.path.isdir(os.path.join(_dev_tools_module._get_workdir(), ".next"))


class DevState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]
    spec: dict
    project_name: str
    run_id: str
    build_attempts: int
    last_build_error: str
    success: bool
    build_command_executed: bool
    build_exit_code: int
    generation_turns: int
    validated_files: List[str]
    file_plan: List[dict]


# ── Pruning sémantique ───────────────────────────────────────────────────────


def _prune_messages(messages: list[BaseMessage]) -> list[BaseMessage]:
    """Garde system messages + premier HumanMessage (spec) + 3 derniers rounds."""
    if len(messages) <= 8:
        return messages

    system_msgs = [m for m in messages if isinstance(m, SystemMessage)]

    # Premier HumanMessage = spec initiale
    first_human: list[BaseMessage] = []
    for m in messages:
        if isinstance(m, HumanMessage):
            first_human = [m]
            break

    # Reconstruit les rounds : AIMessage + ToolMessage(s)/HumanMessage(s) suivants
    rounds: list[list[BaseMessage]] = []
    current: list[BaseMessage] = []
    for msg in messages:
        if isinstance(msg, AIMessage):
            if current:
                rounds.append(current)
            current = [msg]
        elif isinstance(msg, (ToolMessage, HumanMessage)) and current:
            current.append(msg)
    if current:
        rounds.append(current)

    recent = [m for round_ in rounds[-3:] for m in round_]

    seen: set[int] = set()
    result: list[BaseMessage] = []

    def _add(m: BaseMessage) -> None:
        if id(m) not in seen:
            seen.add(id(m))
            result.append(m)

    for m in system_msgs:  _add(m)
    for m in first_human:  _add(m)
    for m in recent:       _add(m)

    return result


def _extract_error_file(error: str) -> str | None:
    """
    Extrait le chemin du premier fichier TS/TSX cité dans une erreur de build.
    Couvre les formats Next.js et tsc :
      - './app/projects/page.tsx'
      - 'app/projects/page.tsx(15,3):'
      - '× app/projects/page.tsx'
    Retourne un chemin relatif (sans ./) ou None.
    """
    import re as _re_err
    patterns = [
        r"\./?(app/[^\s:(]+\.tsx?)",   # ./app/xxx.tsx ou app/xxx.tsx
        r"\./?(lib/[^\s:(]+\.tsx?)",   # ./lib/xxx.ts
        r"\./?(pages/[^\s:(]+\.tsx?)", # ./pages/xxx.tsx (rare)
    ]
    for pat in patterns:
        m = _re_err.search(pat, error)
        if m:
            return m.group(1)
    return None


def _is_build_command(command: str) -> bool:
    cmd = str(command or "").strip().lower()
    return (
        "npm run build" in cmd
        or cmd == "next build"
        or " next build" in cmd
    )


async def run_dev_agent(
    spec: dict,
    project_name: str = "unknown",
    run_id: str = "",
    system_prompt: str = "",
    extra_feedback: str = "",
) -> DevState:
    """Point d'entrée principal du dev agent v4."""

    # ── Isolation workdir par projet ─────────────────────────────────
    # Chaque run travaille dans FACTORY_WORKDIR/<project_name> pour éviter
    # la contamination entre runs (faux succès via .next/ résiduel).
    project_workdir = os.path.join(_BASE_WORKDIR, project_name)
    shutil.rmtree(project_workdir, ignore_errors=True)
    os.makedirs(project_workdir, exist_ok=True)

    # Nettoyage des fichiers résiduels à la racine de _BASE_WORKDIR (anciens runs
    # sans isolation écrivaient package.json etc. directement là).
    # npm remonte les dossiers parents et trouve ces fichiers zombies → EJSONPARSE.
    _STALE_EXTENSIONS = {".json", ".ts", ".tsx", ".js", ".jsx", ".prisma", ".css", ".md"}
    _STALE_NAMED = {".env.local", ".env", "middleware.ts"}
    try:
        for entry in os.listdir(_BASE_WORKDIR):
            full = os.path.join(_BASE_WORKDIR, entry)
            if os.path.isfile(full):
                _, ext = os.path.splitext(entry)
                if ext in _STALE_EXTENSIONS or entry in _STALE_NAMED:
                    os.remove(full)
                    logger.info(f"[dev_graph] résidu racine supprimé : {full}")
    except Exception as _e:
        logger.warning(f"[dev_graph] nettoyage racine non bloquant : {_e}")

    _dev_tools_module.set_workdir(project_workdir)
    logger.info(f"[dev_graph] workdir isolé : {project_workdir}")

    # ── Pré-génération des fichiers templates ────────────────────────
    # package.json, middleware.ts, app/layout.tsx, tsconfig.json, etc.
    # sont écrits depuis les templates de la stack AVANT que le LLM démarre.
    # BLOQUANT : sans package.json, npm install échoue et le run entier est compromis.
    template_written: dict = {}
    _template_error: str = ""
    try:
        from .dev_file_ops import write_template_files
        from agents.stack_config import load_stack_config
        stack_id = spec.get("stack_id", "") or ""
        if not stack_id:
            stack_id = "nextjs-clerk-prisma"
            logger.warning("[dev_graph] stack_id absent de la spec — fallback sur '%s'", stack_id)
        stack_cfg = load_stack_config(stack_id)
        _dev_tools_module.set_forbidden_imports(stack_cfg.get("forbidden_imports", []))
        template_written = write_template_files(project_workdir, stack_cfg, project_name, stack_id, spec=spec)
        logger.info(
            f"[dev_graph] {len(template_written)} fichiers pré-générés depuis templates : "
            f"{list(template_written.keys())}"
        )
    except Exception as _te:
        _template_error = f"write_template_files échoué : {_te}"
        logger.error(f"[dev_graph] {_template_error}")

    if _template_error or "package.json" not in template_written:
        reason = _template_error or "package.json absent des templates"
        logger.error(f"[dev_graph] ABORT — {reason}")
        _dev_tools_module.set_protected_files(None)
        _dev_tools_module.set_workdir(None)
        return {  # type: ignore[return-value]
            "messages": [], "spec": spec, "project_name": project_name, "run_id": run_id,
            "build_attempts": 0, "last_build_error": f"TEMPLATE_FAILURE: {reason}",
            "success": False, "build_command_executed": False,
            "build_exit_code": -1, "validated_files": [],
            "generation_turns": 0, "file_plan": None,
        }

    # ── Materialisation déterministe de schema.prisma depuis ProjectSpec ─────
    # Cause racine traitée:
    # Le LLM oubliait certains modèles (ex: Invoice) dans schema.prisma,
    # ce qui cassait ensuite prisma.invoice / prisma.board (TS2339/TS2305).
    spec_obj = None
    try:
        from agents.project_spec import ProjectSpec

        spec_obj = ProjectSpec(**spec)
        schema_content = spec_obj.to_prisma_schema_block()
        schema_path = os.path.join(project_workdir, "prisma", "schema.prisma")
        os.makedirs(os.path.dirname(schema_path), exist_ok=True)
        with open(schema_path, "w", encoding="utf-8") as f:
            f.write(schema_content)
        template_written["prisma/schema.prisma"] = schema_content
        logger.info(
            f"[dev_graph] schema.prisma matérialisé depuis ProjectSpec "
            f"({len(spec_obj.models)} modèles)"
        )
    except Exception as _se:
        logger.warning(f"[dev_graph] ProjectSpec/schema déterministe non bloquant : {_se}")

    # ── Génération déterministe : pages + loading + error ───────────────────────
    # generate_page_stubs : page.tsx entièrement déterministe pour les pages avec
    #   champ `model` → ajouté à template_written (LLM ne peut pas écraser).
    #   Pour les pages sans `model` : stub auth-guard minimal (LLM peut compléter).
    # generate_page_client_stubs : page-client.tsx avec interface props correcte.
    #   PAS dans template_written → LLM complète le JSX body.
    if spec_obj is not None:
        try:
            from .dev_pages_generator import (
                generate_loading_files,
                generate_error_files,
                generate_root_page_if_needed,
                generate_page_stubs,
                generate_page_client_stubs,
            )
            from .dev_middleware_generator import generate_middleware

            # Middleware dynamique : routes publiques injectées depuis spec.get_public_pages()
            _mw_files = generate_middleware(spec_obj, project_workdir)
            template_written.update(_mw_files)

            # Navigation déterministe : liens depuis spec.pages[] (hors /new et [id])
            from .dev_navigation_generator import generate_navigation
            _nav_files = generate_navigation(spec_obj, project_workdir)
            template_written.update(_nav_files)

            # Page racine déterministe EN PREMIER : doit précéder generate_page_stubs
            # pour que le fichier existe et soit ignoré par generate_page_stubs
            # (qui écrirait sinon un stub `return <div />` non protégé).
            if generate_root_page_if_needed(spec_obj, project_workdir):
                try:
                    with open(os.path.join(project_workdir, "app", "page.tsx"), "r", encoding="utf-8") as _rp:
                        template_written["app/page.tsx"] = _rp.read()
                except Exception:
                    pass

            # Pages entièrement déterministes (model field présent) → template_written
            _page_files = generate_page_stubs(spec_obj, project_workdir)
            template_written.update(_page_files)

            # Stubs page-client déterministes (list UI + create form) → template_written
            # Le planner les exclut ; write_file les protège via _protected.
            _client_stubs = generate_page_client_stubs(spec_obj, project_workdir)
            template_written.update(_client_stubs)

            generate_loading_files(spec_obj, project_workdir)
            generate_error_files(spec_obj, project_workdir)
        except Exception as _pg_err:
            logger.warning(f"[dev_graph] page generators non bloquant : {_pg_err}")

    # ── Génération déterministe : lib/types.ts ───────────────────────
    # Avant pre_run_commands : les page stubs importent @/lib/types.
    # Si prisma generate échoue (early return), les fichiers sont déjà sur disque → TSC correct.
    if spec_obj is not None:
        try:
            from .dev_types_generator import generate_types_file
            _types_result = generate_types_file(spec_obj, project_workdir)
            template_written[_types_result.path] = _types_result.content
            logger.info("[dev_graph] lib/types.ts généré de manière déterministe")
        except Exception as _tg_err:
            logger.warning(f"[dev_graph] types generator non bloquant : {_tg_err}")

    # ── Génération déterministe : lib/schemas.ts ─────────────────────
    if spec_obj is not None:
        try:
            from .dev_zod_generator import generate_schemas_file
            _schemas_result = generate_schemas_file(spec_obj, project_workdir)
            if _schemas_result:
                template_written[_schemas_result.path] = _schemas_result.content
                logger.info("[dev_graph] lib/schemas.ts généré de manière déterministe")
        except Exception as _zg_err:
            logger.warning(f"[dev_graph] zod generator non bloquant : {_zg_err}")

    # ── Génération déterministe : lib/services/*.ts ───────────────────
    # Avant pre_run_commands : les page stubs importent @/lib/services/*.
    if spec_obj is not None:
        try:
            from .dev_service_generator import generate_service_files
            _svc_written = generate_service_files(spec_obj, project_workdir)
            template_written.update(_svc_written)
            logger.info("[dev_graph] %d services DAL générés de manière déterministe", len(_svc_written))
        except Exception as _svc_err:
            logger.warning(f"[dev_graph] service generator non bloquant : {_svc_err}")

    # ── Génération déterministe : app/**/actions.ts ───────────────────
    # Avant pre_run_commands : les page-client stubs importent les actions.
    if spec_obj is not None:
        try:
            from .dev_actions_generator import generate_action_files
            _act_written = generate_action_files(spec_obj, project_workdir)
            template_written.update(_act_written)
            logger.info("[dev_graph] %d fichiers actions.ts générés de manière déterministe", len(_act_written))
        except Exception as _act_err:
            logger.warning(f"[dev_graph] actions generator non bloquant : {_act_err}")

    # Source de vérité unique : tout fichier pré-généré (template_written) est protégé.
    # protected_files du JSON config étend cette liste pour les cas limites (fichiers
    # protégés mais non pré-générés). Les deux sont fusionnés — plus de double gestion.
    _protected = set(template_written.keys()) | set(stack_cfg.get("protected_files", [
        "lib/prisma.ts", "prisma.config.ts", "prisma/schema.prisma", ".eslintrc.stack.json",
    ]))
    _dev_tools_module.set_protected_files(_protected)

    # ── Pre-run commands (T0 refactor — lus depuis stack config) ────────
    # La liste "pre_run_commands" dans nextjs-clerk-prisma.json définit toutes les
    # commandes d'infrastructure pré-LLM. La logique Python ici est stack-agnostique :
    # elle itère, gère les timeouts/erreurs et respecte blocking + requires_prev.
    _pre_run_env = os.environ.copy()
    _pre_run_env["CI"] = "true"
    _pre_run_env.setdefault("DATABASE_URL", "postgresql://user:CHANGEME@localhost:5432/db_placeholder")
    _prev_cmd_ok = True
    for _cmd_spec in stack_cfg.get("pre_run_commands", []):
        _cmd        = _cmd_spec.get("cmd", "")
        _shell      = _cmd_spec.get("shell", True)
        _tout       = _cmd_spec.get("timeout", 120)
        _block      = _cmd_spec.get("blocking", False)
        _needs_prev = _cmd_spec.get("requires_prev", False)
        if not _cmd:
            continue
        if _needs_prev and not _prev_cmd_ok:
            logger.warning("[dev_graph] pre-run '%s' skipped — commande précédente échouée", _cmd)
            continue
        try:
            logger.info("[dev_graph] pre-run : %s ...", _cmd)
            _pr = subprocess.run(
                _cmd, shell=_shell, capture_output=True, text=True,
                timeout=_tout, cwd=project_workdir, env=_pre_run_env,
            )
            if _pr.returncode == 0:
                _prev_cmd_ok = True
                logger.info("[dev_graph] pre-run OK : %s", _cmd)
            else:
                _prev_cmd_ok = False
                _out = (_pr.stdout + _pr.stderr)[:400]
                logger.warning("[dev_graph] pre-run FAILED '%s' (exit %d): %s", _cmd, _pr.returncode, _out)
                if _block:
                    _dev_tools_module.set_protected_files(None)
                    _dev_tools_module.set_workdir(None)
                    return {  # type: ignore[return-value]
                        "messages": [], "spec": spec, "project_name": project_name, "run_id": run_id,
                        "build_attempts": 0, "last_build_error": f"PRE_RUN_FAILED ({_cmd}): {_out[:300]}",
                        "success": False, "build_command_executed": False,
                        "build_exit_code": -1, "validated_files": [], "generation_turns": 0, "file_plan": None,
                    }
        except subprocess.TimeoutExpired:
            _prev_cmd_ok = False
            logger.warning("[dev_graph] pre-run TIMEOUT '%s' (>%ds)", _cmd, _tout)
            if _block:
                _dev_tools_module.set_protected_files(None)
                _dev_tools_module.set_workdir(None)
                return {  # type: ignore[return-value]
                    "messages": [], "spec": spec, "project_name": project_name, "run_id": run_id,
                    "build_attempts": 0, "last_build_error": f"PRE_RUN_TIMEOUT ({_cmd})",
                    "success": False, "build_command_executed": False,
                    "build_exit_code": -1, "validated_files": [], "generation_turns": 0, "file_plan": None,
                }
        except Exception as _cmd_err:
            _prev_cmd_ok = False
            logger.warning("[dev_graph] pre-run exception '%s': %s", _cmd, _cmd_err)

    # ── Service Map (contrat d'interface) ────────────────────────────
    # Les services sont désormais générés par le LLM (pas pré-écrits).
    # On calcule uniquement le service_map string pour l'injecter dans le prompt :
    # le LLM connaît le contrat avant d'écrire chaque service.
    _service_map_str = ""
    if spec_obj is not None:
        try:
            from .dev_service_generator import format_service_map_for_prompt
            _service_map_str = format_service_map_for_prompt(spec_obj)
            logger.info("[dev_graph] Service map calculé (%d modèles)", len(spec_obj.models))
        except Exception as _sg_err:
            logger.warning(f"[dev_graph] service map non bloquant : {_sg_err}")

    # ── Extraction du Type Map Prisma réel ───────────────────────────
    # Après prisma generate, lit node_modules/.prisma/client/index.d.ts
    # pour fournir les types RÉELS au LLM (pas notre reconstruction).
    _prisma_type_map: dict = {}
    if _prev_cmd_ok:
        try:
            from .dev_prisma_extractor import extract_prisma_type_map
            _prisma_type_map = extract_prisma_type_map(project_workdir)
            logger.info("[dev_graph] Type Map Prisma extrait : %d modèles", len(_prisma_type_map))
        except Exception as _pe_err:
            logger.warning(f"[dev_graph] prisma_extractor non bloquant : {_pe_err}")

    # Protéger lib/ (types, schemas, services) + app/**/actions.ts contre réécriture LLM.
    _protected.update(
        k for k in template_written
        if k.startswith("lib/")
        or k.endswith("/actions.ts")
        or k.endswith("page-client.tsx")
    )
    _dev_tools_module.set_protected_files(_protected)

    # ── System prompt ────────────────────────────────────────────────
    if not system_prompt:
        try:
            from .dev_prompts import build_system_prompt
            if spec_obj is None:
                from agents.project_spec import ProjectSpec

                spec_obj = ProjectSpec(**spec)
            system_prompt = build_system_prompt(
                spec_obj,
                pre_written_files=list(template_written.keys()),
                service_map=_service_map_str,
                prisma_type_map=_prisma_type_map,
            )
            logger.info("[dev_graph] System prompt chargé depuis dev_prompts.py")
        except Exception as e:
            logger.warning(f"[dev_graph] dev_prompts non disponible ({e}), fallback minimal")
            system_prompt = (
                "Tu génères un projet Next.js 14 avec Clerk V6 + Prisma 7. "
                "Utilise write_file pour écrire les fichiers, "
                "shell_exec pour tsc et npm build. "
                "Génère tous les fichiers nécessaires puis build."
            )

    # ── Outils ───────────────────────────────────────────────────────
    tools = list(DEV_TOOLS) + [web_search]

    logger.info(f"[dev_graph] {len(tools)} outils : {[t.name for t in tools]}")

    # ── Règles de rôle depuis la config stack (SSoT) ─────────────────
    # code_role_hints dans nextjs-clerk-prisma.json — chaque valeur est une liste de strings.
    _hints_raw = stack_cfg.get("code_role_hints", {})
    _role_rules_from_config: dict[str, str] = {
        role: "\n".join(lines) for role, lines in _hints_raw.items()
    } if _hints_raw else {}

    _dev_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    llm = ChatOpenAI(model=_dev_model, temperature=0, max_retries=3)
    # llm_with_tools est construit dynamiquement dans executor_node selon la phase.

    # Cache RAG par rôle — lifetime = ce run. Partagé par toutes les invocations
    # d'executor_node via closure. Évite N requêtes Qdrant identiques pour N fichiers
    # du même rôle (ex: 8 pages → 1 seule requête Qdrant au lieu de 8).
    _rag_cache: dict[str, str] = {}

    # ── Planificateur deterministe (Plan-and-Execute) ─────────────────────
    def planner_node(state: DevState) -> dict:
        """Genere le plan une seule fois au demarrage."""
        if state.get("file_plan"):
            return {}  # plan deja genere
        from agents.planner import make_deterministic_plan, validate_plan
        from agents.project_spec import ProjectSpec as _PS
        try:
            _spec_local = _PS(**state.get("spec", {}))
        except Exception as _pe:
            logger.error("[planner] ProjectSpec invalide — plan vide : %s", _pe)
            return {"file_plan": None}  # None = signal d'échec (distinct de [] = plan vide légitime)
        _tpl = list(template_written.keys())
        _plan = make_deterministic_plan(_spec_local, _tpl)
        _missing = validate_plan(_plan, _spec_local, _tpl)
        if _missing:
            logger.warning("[planner] fichiers non couverts par le plan : %s", _missing)
        _plan_dicts = [e.model_dump() for e in _plan]
        logger.info("[planner] %d fichiers planes : %s", len(_plan_dicts),
                    [e["path"] for e in _plan_dicts])
        return {"file_plan": _plan_dicts}

    # ── Nœud dev principal ───────────────────────────────────────────
    def executor_node(state: DevState) -> dict:
        # Pruning sémantique : élimine le bruit accumulé (vieux write_file OK,
        # anciens échanges de génération) tout en gardant les éléments critiques
        # (SystemMessage, spec initiale, 3 derniers rounds, dernière correction).
        messages = _prune_messages(list(state["messages"]))

        # Plan cursor : prochain fichier a generer.
        # Source de vérité = filesystem : si le fichier existe sur disque, il a été écrit.
        # Indépendant de validated_files (supprimé avec PV) — robuste aux redémarrages.
        _plan = state.get("file_plan") or []  # None (échec planner) ou [] traités pareil
        _plan_failed = state.get("file_plan") is None  # planner a levé une exception
        _next_entry = next(
            (e for e in _plan if not os.path.exists(os.path.join(project_workdir, e["path"]))),
            None,
        )
        # Pour example-anchor : fichiers du plan déjà présents sur disque
        _written_set = {e["path"] for e in _plan if os.path.exists(os.path.join(project_workdir, e["path"]))}

        # Injection sur erreur build.
        last_error = state.get("last_build_error", "")
        if last_error:
            # Extrait les lignes d'erreur TS (filtre le bruit webpack/Next)
            _ts_lines = [
                l for l in last_error.splitlines()
                if any(kw in l for kw in ("error TS", "Type error", "×", "⨯", "→", ".tsx", ".ts"))
            ]
            _err_excerpt = "\n".join((_ts_lines or last_error.splitlines())[:12])[:700]

            # Lit le contenu du fichier incriminé pour donner au LLM le contexte complet
            _file_ctx = ""
            _err_file = _extract_error_file(last_error)
            if _err_file:
                _err_abs = os.path.join(project_workdir, _err_file)
                if os.path.exists(_err_abs):
                    try:
                        with open(_err_abs, "r", encoding="utf-8") as _ef:
                            _file_lines = _ef.readlines()[:40]
                        _numbered = "".join(f"{i+1:3} | {l}" for i, l in enumerate(_file_lines))
                        _file_ctx = f"\nContenu actuel de {_err_file} :\n```typescript\n{_numbered}```\n"
                    except Exception:
                        pass

            messages.append(HumanMessage(content=(
                f"ERREUR BUILD à corriger :\n{_err_excerpt}"
                f"{_file_ctx}\n"
                "1. Identifie la ligne exacte dans le fichier ci-dessus.\n"
                "2. Corrige avec write_file (réécriture complète du fichier uniquement si nécessaire).\n"
                "3. shell_exec('npx tsc --noEmit') — si OK → shell_exec('npm run build')"
            )))

        # Plan-and-Execute : guidage fichier par fichier.
        else:
            if _plan_failed:
                # Plan non généré (spec invalide) — arrêt immédiat sans appel LLM.
                # tools_condition verra un HumanMessage comme dernier message → __end__.
                logger.error("[executor] plan_failed=True — arrêt immédiat BUILD_FAILED")
                return {
                    "last_build_error": "PLAN_FAILED: spec invalide — plan non généré",
                    "build_command_executed": True,
                    "build_attempts": MAX_BUILD_ATTEMPTS,
                    "success": False,
                }
            elif _next_entry is None:
                # Tous les fichiers du plan couverts OU plan vide (Option A : tout pré-généré).
                # Dans les deux cas → déclencher le build.
                if not _plan:
                    logger.info("[executor] plan vide (tout pré-généré par templates) — déclenchement build direct")
                messages.append(HumanMessage(content=(
                    f"Tous les {len(_plan)} fichiers du plan ont ete ecrits. "
                    "Execute maintenant dans cet ordre EXACT :\n"
                    "1. shell_exec('npx prisma generate')\n"
                    "2. shell_exec('npm run build')\n"
                    "Ne genere pas d'autres fichiers avant d'avoir lance le build."
                )))
            else:
                from .dev_context import build_role_context
                _role = _next_entry.get("role", "")
                _hint = _next_entry.get("context_hint", "")
                _path = _next_entry["path"]

                _rule = _role_rules_from_config.get(_role, "")
                _ctx = (
                    f"CONTEXTE : {_hint}\n\nREGLE {_role.upper()} :\n{_rule}"
                    if _rule else f"CONTEXTE : {_hint}"
                )

                # Dépendances disque + standard RAG ciblé sur ce rôle (dev_context.py).
                _dep = build_role_context(_role, _path, spec_obj, project_workdir, _service_map_str, cache=_rag_cache)

                # Phase 8 — Example-anchored prompting.
                # Injecte le dernier fichier écrit du même rôle comme exemple concret.
                # Ancre le LLM sur un pattern déjà produit plutôt qu'une règle abstraite.
                _example_anchor = ""
                if _written_set:
                    _same_role_candidates = [
                        e for e in _plan
                        if e.get("role") == _role and e["path"] in _written_set
                    ]
                    if _same_role_candidates:
                        _example_path = _same_role_candidates[-1]["path"]
                        _example_abs = os.path.join(project_workdir, _example_path)
                        try:
                            with open(_example_abs, "r", encoding="utf-8") as _ef:
                                _example_content = _ef.read()[:500]
                            _example_anchor = (
                                f"\nEXEMPLE VALIDE ({_example_path} — pattern à réutiliser) :\n"
                                f"```typescript\n{_example_content}\n```\n"
                            )
                        except Exception:
                            pass

                messages.append(HumanMessage(content=(
                    f"{_ctx}{_dep}{_example_anchor}\n\n"
                    f"Ecris maintenant le fichier : {_path}\n"
                    "Un seul write_file. Rien d'autre."
                )))

        llm_with_tools = llm.bind_tools(tools)

        response = llm_with_tools.invoke(messages)

        return {
            "messages": [response],
            "generation_turns": int(state.get("generation_turns", 0) or 0) + 1,
        }

    # ── Extraction erreur + détection succès déterministe ────────────
    def extract_build_error_node(state: DevState) -> dict:
        """
        Détecte le succès/échec du build Next.js en corrélant chaque ToolMessage
        avec le command de l'AIMessage via tool_call_id.

        Source unique de vérité : exit code retourné par shell_exec.
          "OK\n..."       → exit code 0  → build_success = True
          "FAILED (exit N)..." → exit code N → build_success = False
        Zéro keyword matching sur le contenu de la sortie.
        """
        from langchain_core.messages import ToolMessage
        import re as _re

        # Étape 1 — construire la map tool_call_id → command depuis tous les AIMessages.
        # Permet de savoir, pour chaque ToolMessage, quelle commande l'a produit.
        tool_call_commands: dict[str, str] = {}
        for msg in state["messages"]:
            if isinstance(msg, AIMessage):
                for call in (getattr(msg, "tool_calls", None) or []):
                    call_id = call.get("id", "")
                    if not call_id:
                        continue
                    args = call.get("args", {})
                    cmd = str(args.get("command", "") if isinstance(args, dict) else args or "")
                    tool_call_commands[call_id] = cmd

        last_error = ""
        build_succeeded = False
        build_executed = False
        build_exit = -1

        # Étape 2 — scanner les ToolMessages en remontant, filtrer sur les build commands.
        for msg in reversed(state["messages"]):
            if not isinstance(msg, ToolMessage):
                continue
            content = str(getattr(msg, "content", "") or "")
            call_id = getattr(msg, "tool_call_id", "") or ""
            cmd = tool_call_commands.get(call_id, "")

            if not _is_build_command(cmd):
                continue  # tsc, prisma, npm install, etc. — pas un build

            build_executed = True

            # Succès : exit code 0 — préfixe "OK\n" de shell_exec, point final
            if content.startswith("OK\n"):
                build_succeeded = True
                build_exit = 0
                break

            # Échec : préfixe "FAILED (exit N)" de shell_exec
            last_error = content[:3000]
            m = _re.search(r"FAILED \(exit (\d+)\)", content)
            build_exit = int(m.group(1)) if m else 1
            break

        # Hardening : build command dans un AIMessage sans ToolMessage associé
        # (output tronqué, tool error intercepté par ToolNode, etc.).
        if not build_executed:
            for msg in reversed(state["messages"]):
                if isinstance(msg, AIMessage):
                    for call in (getattr(msg, "tool_calls", None) or []):
                        args = call.get("args", {})
                        cmd = str(args.get("command", "") if isinstance(args, dict) else args or "")
                        if _is_build_command(cmd):
                            build_executed = True
                            build_exit = 1  # conservatif — pas de succès sans ToolMessage
                            logger.warning(
                                "[extract_error] build command dans AIMessage sans ToolMessage associé "
                                "— output manquant ou tronqué"
                            )
                    break

        new_attempts = int(state.get("build_attempts", 0) or 0) + (1 if build_executed else 0)

        return {
            "last_build_error": last_error,
            "success": build_succeeded,
            "build_command_executed": build_executed,
            "build_exit_code": build_exit,
            "build_attempts": new_attempts,
        }

    # ── Routage ──────────────────────────────────────────────────────
    def route_after_tools(state: DevState) -> str:
        # Action 5 : validation légère des champs critiques du state.
        # Un type inattendu (ex: str au lieu d'int) causerait une boucle silencieuse.
        for _field, _expected in (("build_attempts", int), ("generation_turns", int)):
            _val = state.get(_field)
            if _val is not None and not isinstance(_val, _expected):
                logger.error(
                    "[route_after_tools] state['%s'] type invalide : %s (attendu %s) — arrêt",
                    _field, type(_val).__name__, _expected.__name__,
                )
                return END

        if state.get("success", False):
            return END

        # F-08: circuit breaker — limite le nombre de tours de génération (hors correction build)
        turns = int(state.get("generation_turns", 0) or 0)
        if turns >= MAX_GENERATION_TURNS:
            logger.warning(
                "[dev_graph] MAX_GENERATION_TURNS=%d atteint — arrêt boucle génération",
                MAX_GENERATION_TURNS,
            )
            return END

        last_error = state.get("last_build_error", "")
        if last_error:
            # Boucle de correction : le LLM reçoit la correction ciblée (Faille 4)
            # et corrige dans la phase "correction" (Faille 3).
            # Limite : MAX_BUILD_ATTEMPTS tentatives avant d'abandonner.
            attempts = int(state.get("build_attempts", 0) or 0)
            if attempts >= MAX_BUILD_ATTEMPTS:
                logger.warning(
                    "[dev_graph] MAX_BUILD_ATTEMPTS=%d atteint — arrêt boucle correction",
                    MAX_BUILD_ATTEMPTS,
                )
                return END
            return "executor"

        # LLM n'a pas encore lancé de build — continuer.
        # La sécurité contre les boucles infinies est assurée par recursion_limit=150
        # + l'injection A1 ("build maintenant") dans dev_node qui guide le LLM vers le build.
        return "executor"

    # ── Progressive Validation (Étape 2) ─────────────────────────────
    # Nœud intercalé entre tools et extract_error.
    # Après chaque batch de tool calls, détecte les fichiers .ts/.tsx écrits,
    # lance tsc --noEmit, filtre les erreurs sur ces fichiers uniquement.
    # Si erreurs → injection HumanMessage ciblé → retour au LLM pour correction immédiate.
    # Si clean   → pass-through vers extract_error (flux normal).
    #
    # Pourquoi ici et pas dans write_file :
    #   - write_file est un outil atomique — il ne doit pas piloter le graph
    #   - Un nœud LangGraph est le seul endroit correct pour décider du routage
    #   - On valide le batch (plusieurs fichiers d'un tour) plutôt que chaque write isolé

    # ── Assemblage du graph ──────────────────────────────────────────
    builder = StateGraph(DevState)
    builder.add_node("planner", planner_node)
    builder.add_node("executor", executor_node)
    builder.add_node("tools", ToolNode(tools, handle_tool_errors=True))
    builder.add_node("extract_error", extract_build_error_node)

    builder.add_edge(START, "planner")
    builder.add_edge("planner", "executor")
    builder.add_conditional_edges("executor", tools_condition, {
        "tools": "tools",
        "__end__": END,
    })
    builder.add_edge("tools", "extract_error")
    builder.add_conditional_edges("extract_error", route_after_tools, {
        "executor": "executor",
        END: END,
    })

    graph = builder.compile()

    # ── State initial ─────────────────────────────────────────────────
    spec_models = [m.get("name", "") for m in spec.get("models", [])]
    spec_pages = [p.get("path", "") for p in spec.get("pages", [])]
    # Webhooks seulement — les routes CRUD sont des Server Actions.
    # Les montrer ici ferait croire au LLM qu'il doit créer des route.ts pour chaque mutation.
    spec_webhooks = [
        f"{r.get('method','')} {r.get('path','')}"
        for r in spec.get("routes", [])
        if "webhook" in r.get("path", "").lower() or "stripe" in r.get("path", "").lower()
    ]

    initial_state: DevState = {
        "messages": [
            SystemMessage(content=system_prompt),
            HumanMessage(content=(
                f"Génère le projet '{project_name}'.\n\n"
                f"Modèles Prisma : {spec_models}\n"
                f"Pages à générer : {spec_pages}\n"
                + (f"Webhooks (route.ts requis) : {spec_webhooks}\n" if spec_webhooks else "")
                + f"\nFingerprint spec : {spec.get('spec_fingerprint', 'n/a')}\n"
                "⚠️ Les Server Actions (app/**/actions.ts) sont PRÉ-GÉNÉRÉES — "
                "NE PAS les réécrire. Génère uniquement les pages (app/**/page.tsx)."
            )),
            *([HumanMessage(content=extra_feedback)] if extra_feedback else []),
        ],
        "spec": spec,
        "project_name": project_name,
        "run_id": run_id,
        "build_attempts": 0,
        "last_build_error": "",
        "success": False,
        "build_command_executed": False,
        "build_exit_code": -1,
        "generation_turns": 0,
        "validated_files": [],
        "file_plan": None,  # None = non encore généré; planner_node le remplit
    }

    try:
        result = await graph.ainvoke(initial_state, {"recursion_limit": 100})

        # ── Signal de succès unique : build_command_executed + build_exit_code == 0 ──
        # Phase B : on ne surcharge plus le résultat depuis .next/ sur disque.
        # .next/ est logué comme signal secondaire uniquement (détection d'anomalie).
        disk_next = _check_next_dir_on_disk()
        final_success = bool(result.get("success", False))

        # ── Quality check AST (non bloquant) ────────────────────────────────────
        # Lancé seulement si le build a réussi (node_modules + code final disponibles).
        # Détecte Z21-Z26 : N+1, pagination, select manquant, transaction manquante.
        quality_violations: list[dict] = []
        quality_violations_count = 0
        if final_success:
            try:
                from agents.core.quality_validator import run_quality_check
                _qr = await run_quality_check(project_workdir)
                if _qr.status == "failed":
                    quality_violations = [
                        {
                            "rule": v.rule_id,
                            "file": v.file,
                            "line": v.line,
                            "reason": v.reason,
                        }
                        for v in (_qr.violations or [])
                    ]
                    quality_violations_count = len(quality_violations)
                    logger.info(
                        "[quality_check] %d violation(s) — %s",
                        quality_violations_count,
                        [v["rule"] for v in quality_violations],
                    )
                elif _qr.status == "ok":
                    logger.info("[quality_check] aucune violation qualité détectée")
                else:
                    logger.info("[quality_check] status=%s — %s", _qr.status, (_qr.evidence or "")[:120])
            except Exception as _qe:
                logger.warning("[quality_check] échec non bloquant : %s", _qe)

        result = dict(result)
        result["quality_violations"] = quality_violations
        result["quality_violations_count"] = quality_violations_count
        build_executed = bool(result.get("build_command_executed", False))

        if disk_next and not final_success:
            logger.warning(
                "[dev_graph] ANOMALIE — .next/ présent mais success=False "
                "(build non exécuté ou erreur non capturée) — succès non accordé"
            )
        if final_success and not build_executed:
            # Ne devrait plus arriver avec Phase B, mais on le trace
            logger.error(
                "[dev_graph] INCOHÉRENCE — success=True mais build_command_executed=False"
            )

        logger.info(
            f"[dev_graph] terminé — success={final_success} "
            f"| build_executed={build_executed} "
            f"| build_exit_code={result.get('build_exit_code', -1)} "
            f"| build_attempts={result.get('build_attempts', 0)} "
            f"| .next/={disk_next} "
            f"| workdir={project_workdir}"
        )

        return result
    finally:
        # Toujours réinitialiser — même en cas d'exception
        _dev_tools_module.set_protected_files(None)
        _dev_tools_module.set_workdir(None)
