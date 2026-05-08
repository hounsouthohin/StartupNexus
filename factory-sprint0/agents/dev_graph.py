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

import agents.dev_tools as _dev_tools_module
from agents.dev_tools import write_file, read_file, list_directory, shell_exec, file_exists
from agents.web_search import web_search

logger = logging.getLogger(__name__)

import re as _re_utils


def _pascal_to_kebab_local(name: str) -> str:
    """PascalCase → kebab-case. Ex: LeaveRequest → leave-request."""
    return _re_utils.sub(r"(?<!^)(?=[A-Z])", "-", name).lower()


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
    """Garde system messages + premier HumanMessage (spec) + 5 derniers rounds."""
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

    recent = [m for round_ in rounds[-5:] for m in round_]

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
        from agents.dev_file_ops import write_template_files
        from agents.stack_config import load_stack_config
        stack_id = spec.get("stack_id", "") or "nextjs-clerk-prisma"
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

    # ── Génération déterministe : loading.tsx ───────────────────────────────────
    # generate_page_stubs retiré : les stubs étaient écrasés par le LLM de toute façon.
    # generate_loading_files produit app/<path>/loading.tsx pour les pages protégées.
    if spec_obj is not None:
        try:
            from agents.dev_pages_generator import (
                generate_loading_files,
                generate_error_files,
                generate_root_page_if_needed,
            )
            generate_loading_files(spec_obj, project_workdir)
            generate_error_files(spec_obj, project_workdir)
            # Page racine déterministe : si '/' est dans le spec sans pages_detail,
            # on génère un redirect Python pour éviter que le LLM improvise un dashboard
            # qui accèderait à des relations inexistantes dans SerializedXxx (→ TS2551).
            if generate_root_page_if_needed(spec_obj, project_workdir):
                try:
                    with open(os.path.join(project_workdir, "app", "page.tsx"), "r", encoding="utf-8") as _rp:
                        template_written["app/page.tsx"] = _rp.read()
                except Exception:
                    pass
        except Exception as _pg_err:
            logger.warning(f"[dev_graph] page generators non bloquant : {_pg_err}")

    # Protéger uniquement l'infrastructure — le code applicatif appartient au LLM.
    _protected = {
        "lib/prisma.ts",
        "prisma.config.ts",
        "prisma/schema.prisma",
        ".eslintrc.stack.json",
    }
    _dev_tools_module.set_protected_files(_protected)

    # ── npm install (Python pre-run, hors LLM) ──────────────────────
    # npm install est de l'infrastructure — trop critique pour être déléguée au LLM.
    # Exécutée ici avec un timeout généreux (5 min) avant que le LLM démarre.
    # Le LLM garde uniquement `node_modules/.bin/prisma generate` (après schema.prisma).
    _npm_prerun_ok = False
    try:
        logger.info(f"[dev_graph] npm install pre-run dans {project_workdir} ...")
        _npm_result = subprocess.run(
            "npm install",
            shell=True,
            capture_output=True,
            text=True,
            timeout=300,
            cwd=project_workdir,
        )
        if _npm_result.returncode == 0:
            _npm_prerun_ok = True
            logger.info("[dev_graph] npm install pre-run OK")
        else:
            logger.warning(
                f"[dev_graph] npm install pre-run FAILED (exit {_npm_result.returncode}): "
                f"{(_npm_result.stdout + _npm_result.stderr)[:400]}"
            )
    except subprocess.TimeoutExpired:
        logger.warning("[dev_graph] npm install pre-run TIMEOUT (>300s)")
    except Exception as _npm_err:
        logger.warning(f"[dev_graph] npm install pre-run exception : {_npm_err}")

    # ── prisma generate (Python pre-run, hors LLM) ───────────────────
    # prisma generate est BLOQUANT si npm install a réussi :
    # sans @prisma/client généré, tout import 'from @prisma/client' échoue (TS2305).
    if _npm_prerun_ok:
        try:
            logger.info(f"[dev_graph] prisma generate pre-run dans {project_workdir} ...")
            _prisma_env = os.environ.copy()
            _prisma_env["CI"] = "true"
            _prisma_env.setdefault("DATABASE_URL", "postgresql://user:CHANGEME@localhost:5432/db_placeholder")
            _prisma_result = subprocess.run(
                "npx prisma generate",
                shell=True,
                capture_output=True,
                text=True,
                cwd=project_workdir,
                timeout=120,
                env=_prisma_env,
            )
            if _prisma_result.returncode == 0:
                logger.info("[dev_graph] prisma generate pre-run OK")
            else:
                _pg_out = (_prisma_result.stdout + _prisma_result.stderr)[:600]
                logger.error(
                    f"[dev_graph] prisma generate FAILED (exit {_prisma_result.returncode}): {_pg_out}"
                )
                _dev_tools_module.set_protected_files(None)
                _dev_tools_module.set_workdir(None)
                return {  # type: ignore[return-value]
                    "messages": [], "spec": spec, "project_name": project_name, "run_id": run_id,
                    "build_attempts": 0,
                    "last_build_error": f"PRISMA_GENERATE_FAILED: {_pg_out[:300]}",
                    "success": False, "build_command_executed": False,
                    "build_exit_code": -1, "validated_files": [],
                    "generation_turns": 0, "file_plan": None,
                }
        except subprocess.TimeoutExpired:
            logger.warning("[dev_graph] prisma generate pre-run TIMEOUT (>120s) — non bloquant")
        except Exception as _pg_err:
            logger.warning(f"[dev_graph] prisma generate pre-run exception (non bloquant) : {_pg_err}")
    else:
        logger.warning("[dev_graph] prisma generate skipped — npm install a échoué")

    # ── Génération déterministe : lib/types.ts ───────────────────────
    # Écrit avant que le LLM démarre — le LLM ne touche plus lib/types.ts.
    # Source de vérité des DTOs Create/Update pour tous les services et routes.
    if spec_obj is not None:
        try:
            from agents.dev_types_generator import generate_types_file
            _types_result = generate_types_file(spec_obj, project_workdir)
            template_written[_types_result.path] = _types_result.content
            logger.info("[dev_graph] lib/types.ts généré de manière déterministe")
        except Exception as _tg_err:
            logger.warning(f"[dev_graph] types generator non bloquant : {_tg_err}")

    # ── Service Map (contrat d'interface) ────────────────────────────
    # Les services sont désormais générés par le LLM (pas pré-écrits).
    # On calcule uniquement le service_map string pour l'injecter dans le prompt :
    # le LLM connaît le contrat avant d'écrire chaque service.
    _service_map_str = ""
    if spec_obj is not None:
        try:
            from agents.dev_service_generator import format_service_map_for_prompt
            _service_map_str = format_service_map_for_prompt(spec_obj)
            logger.info("[dev_graph] Service map calculé (%d modèles)", len(spec_obj.models))
        except Exception as _sg_err:
            logger.warning(f"[dev_graph] service map non bloquant : {_sg_err}")

    # ── Génération déterministe : lib/schemas.ts ─────────────────────
    # Schémas Zod alignés sur lib/types.ts — utilisés dans les Server Actions.
    if spec_obj is not None:
        try:
            from agents.dev_zod_generator import generate_schemas_file
            _schemas_result = generate_schemas_file(spec_obj, project_workdir)
            if _schemas_result:
                template_written[_schemas_result.path] = _schemas_result.content
                logger.info("[dev_graph] lib/schemas.ts généré de manière déterministe")
        except Exception as _zg_err:
            logger.warning(f"[dev_graph] zod generator non bloquant : {_zg_err}")

    # ── Génération déterministe : lib/services/*.ts ───────────────────
    # Base CRUD pré-générée pour chaque modèle Prisma — socle correct garanti par Python.
    # NON protégé : le LLM peut ajouter des méthodes enrichies (ex: getTasksByProject).
    # Le planner exclut automatiquement ces fichiers car ils sont dans template_written.
    if spec_obj is not None:
        try:
            from agents.dev_service_generator import generate_service_files
            _svc_written = generate_service_files(spec_obj, project_workdir)
            template_written.update(_svc_written)
            logger.info("[dev_graph] %d services DAL générés de manière déterministe", len(_svc_written))
        except Exception as _svc_err:
            logger.warning(f"[dev_graph] service generator non bloquant : {_svc_err}")

    # ── Génération déterministe : app/**/actions.ts ───────────────────
    # Server Actions CRUD pré-générées par modèle : auth guard + Zod + service call.
    # Élimine TS2304 (import manquants), TS2345 (types incompatibles) et auth oubliés.
    # Protégées contre réécriture LLM — le LLM peut en AJOUTER d'autres mais pas écraser.
    _action_map_str = ""
    if spec_obj is not None:
        try:
            from agents.dev_actions_generator import generate_action_files, format_action_map_for_prompt
            _act_written = generate_action_files(spec_obj, project_workdir)
            template_written.update(_act_written)
            _action_map_str = format_action_map_for_prompt(spec_obj)
            logger.info("[dev_graph] %d fichiers actions.ts générés de manière déterministe", len(_act_written))
        except Exception as _act_err:
            logger.warning(f"[dev_graph] actions generator non bloquant : {_act_err}")

    # ── Extraction du Type Map Prisma réel ───────────────────────────
    # Après prisma generate, lit node_modules/.prisma/client/index.d.ts
    # pour fournir les types RÉELS au LLM (pas notre reconstruction).
    _prisma_type_map: dict = {}
    if _npm_prerun_ok:
        try:
            from agents.dev_prisma_extractor import extract_prisma_type_map
            _prisma_type_map = extract_prisma_type_map(project_workdir)
            logger.info("[dev_graph] Type Map Prisma extrait : %d modèles", len(_prisma_type_map))
        except Exception as _pe_err:
            logger.warning(f"[dev_graph] prisma_extractor non bloquant : {_pe_err}")

    # Protéger lib/ (types, schemas, services) + app/**/actions.ts contre réécriture LLM.
    _protected.update(
        k for k in template_written
        if k.startswith("lib/") or k.endswith("/actions.ts")
    )
    _dev_tools_module.set_protected_files(_protected)

    # ── System prompt ────────────────────────────────────────────────
    if not system_prompt:
        try:
            from agents.dev_prompts import build_system_prompt
            if spec_obj is None:
                from agents.project_spec import ProjectSpec

                spec_obj = ProjectSpec(**spec)
            system_prompt = build_system_prompt(
                spec_obj,
                pre_written_files=list(template_written.keys()),
                service_map=_service_map_str,
                action_map=_action_map_str,
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

    _dev_model = os.getenv("OPENAI_MODEL", "gpt-4o")
    llm = ChatOpenAI(model=_dev_model, temperature=0, max_retries=3)
    # llm_with_tools est construit dynamiquement dans executor_node selon la phase.

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
                # Plan non généré (spec invalide) — ne pas déclencher le build à vide
                logger.error("[executor] plan_failed=True — run en mode sans plan (LLM libre)")
            elif _next_entry is None and not _plan:
                # Plan vide ET aucun fichier validé : anomalie
                logger.error("[executor] plan vide et aucun fichier validé — run sans guidage")
            elif _next_entry is None:
                # Tous les fichiers valides : declencher le build
                messages.append(HumanMessage(content=(
                    f"Tous les {len(_plan)} fichiers du plan ont ete ecrits. "
                    "Execute maintenant dans cet ordre EXACT :\n"
                    "1. shell_exec('npx prisma generate')\n"
                    "2. shell_exec('npm run build')\n"
                    "Ne genere pas d'autres fichiers avant d'avoir lance le build."
                )))
            else:
                _role = _next_entry.get("role", "")
                _hint = _next_entry.get("context_hint", "")
                _path = _next_entry["path"]

                _rule = _role_rules_from_config.get(_role, "")
                _ctx = (
                    f"CONTEXTE : {_hint}\n\nREGLE {_role.upper()} :\n{_rule}"
                    if _rule else f"CONTEXTE : {_hint}"
                )

                # Lecture des dependances utiles depuis le disque.
                # Service : lib/types.ts + lib/prisma.ts.
                # Actions : schemas.ts + service correspondant (LLM-généré ou disque).
                # Route   : types.ts (800 chars) + service correspondant.
                # Page    : service correspondant (400 chars).
                _dep = ""
                if _role == "service":
                    _types_abs = os.path.join(project_workdir, "lib", "types.ts")
                    if os.path.exists(_types_abs):
                        try:
                            with open(_types_abs, "r", encoding="utf-8") as _f:
                                _dep += (
                                    f"\nlib/types.ts :\n"
                                    f"```typescript\n{_f.read()[:800]}\n```"
                                )
                        except Exception:
                            pass
                    _prisma_abs = os.path.join(project_workdir, "lib", "prisma.ts")
                    if os.path.exists(_prisma_abs):
                        try:
                            with open(_prisma_abs, "r", encoding="utf-8") as _f:
                                _dep += (
                                    f"\nlib/prisma.ts :\n"
                                    f"```typescript\n{_f.read()[:250]}\n```"
                                )
                        except Exception:
                            pass
                elif _role == "actions":
                    # Service Map compact (closure — toujours disponible si services générés)
                    if _service_map_str:
                        _dep += f"\n{_service_map_str}"
                    # schemas.ts (schémas Zod pour la validation dans les actions)
                    _schemas_abs = os.path.join(project_workdir, "lib", "schemas.ts")
                    if os.path.exists(_schemas_abs):
                        try:
                            with open(_schemas_abs, "r", encoding="utf-8") as _f:
                                _dep += (
                                    f"\nlib/schemas.ts :\n"
                                    f"```typescript\n{_f.read()[:600]}\n```"
                                )
                        except Exception:
                            pass
                    # Chercher le service correspondant au segment du fichier actions.ts
                    # ex: app/projects/actions.ts → lib/services/project.service.ts
                    _act_seg = _path.split("/")[-2] if "/" in _path else ""
                    # F-04: utiliser l'index modèles pour une correspondance stable
                    _act_match = next(
                        (m for m in (spec_obj.models if spec_obj else [])
                         if _pascal_to_kebab_local(m.name) == _act_seg
                         or _pascal_to_kebab_local(m.name) + "s" == _act_seg),
                        None,
                    )
                    _svc_candidates = (
                        [_pascal_to_kebab_local(_act_match.name)]
                        if _act_match else [_act_seg, _act_seg.rstrip("s")]
                    )
                    for _sv in _svc_candidates:
                        _svc_abs = os.path.join(project_workdir, "lib", "services",
                                                f"{_sv}.service.ts")
                        if os.path.exists(_svc_abs):
                            try:
                                with open(_svc_abs, "r", encoding="utf-8") as _f:
                                    _dep += (
                                        f"\nlib/services/{_sv}.service.ts :\n"
                                        f"```typescript\n{_f.read()[:500]}\n```"
                                    )
                            except Exception:
                                pass
                            break
                elif _role == "route":
                    # types.ts — pré-généré sur disque, pas dans validated_files
                    _types_abs = os.path.join(project_workdir, "lib", "types.ts")
                    if os.path.exists(_types_abs):
                        try:
                            with open(_types_abs, "r", encoding="utf-8") as _f:
                                _dep = (
                                    f"\nlib/types.ts :\n"
                                    f"```typescript\n{_f.read()[:800]}\n```"
                                )
                        except Exception:
                            pass
                    # Service correspondant : app/api/{seg}/route.ts → lib/services/{seg}.service.ts
                    _route_seg = _path.split("/")
                    _seg_candidates = []
                    for _s in _route_seg:
                        if _s not in ("app", "api", "route.ts", "") and not _s.startswith("["):
                            _seg_candidates.append(_s)
                    for _seg in reversed(_seg_candidates):
                        _svc_tries = [_seg, _seg.rstrip("s")]
                        for _sv in _svc_tries:
                            _svc_abs = os.path.join(project_workdir, "lib", "services",
                                                    f"{_sv}.service.ts")
                            if os.path.exists(_svc_abs):
                                try:
                                    with open(_svc_abs, "r", encoding="utf-8") as _f:
                                        _dep += (
                                            f"\nlib/services/{_sv}.service.ts :\n"
                                            f"```typescript\n{_f.read()[:600]}\n```"
                                        )
                                except Exception:
                                    pass
                                break
                        if _dep and "service.ts" in _dep:
                            break
                elif _role == "page_client":
                    # Injection du actions.ts parent : le LLM DOIT voir la signature ET
                    # le chemin d'import relatif EXACT avant d'écrire le Client Component.
                    # Ex: app/projects/new/page-client.tsx → actions à app/projects/actions.ts
                    # → chemin relatif = '../actions' (1 niveau au-dessus), PAS './actions'.
                    _client_dir_parts = _path.split("/")[:-1]  # ['app', 'projects', 'new']
                    # Remonte l'arborescence jusqu'à trouver un actions.ts
                    for _depth in range(len(_client_dir_parts), 1, -1):
                        _act_rel = "/".join(_client_dir_parts[:_depth]) + "/actions.ts"
                        _act_abs = os.path.join(project_workdir, _act_rel)
                        if os.path.exists(_act_abs):
                            try:
                                # Chemin d'import relatif selon profondeur de la page-client
                                _depth_diff = len(_client_dir_parts) - _depth
                                _rel_import = ("../" * _depth_diff + "actions") if _depth_diff > 0 else "./actions"
                                with open(_act_abs, "r", encoding="utf-8") as _af:
                                    _dep += (
                                        f"\nactions.ts (chemin d'import relatif EXACT : '{_rel_import}') :\n"
                                        f"```typescript\n{_af.read()[:600]}\n```\n"
                                        f"⚠️  IMPORT OBLIGATOIRE : import {{ createXxx, deleteXxx }} from '{_rel_import}'\n"
                                        f"⚠️  APPELS CORRECTS :\n"
                                        f"  create/update → FormData : const fd = new FormData(); fd.set('field', val); await createXxx(fd)\n"
                                        f"  delete → ID string : await deleteXxx(item.id)   ← PAS FormData, PAS objet plain"
                                    )
                            except Exception:
                                pass

                            # Injection du type SerializedXxx correspondant depuis lib/types.ts.
                            # Le LLM doit voir les champs EXACTS disponibles pour éviter
                            # d'inventer des champs (ex: submissionDate) qui n'existent pas → TS2339.
                            try:
                                from agents.dev_actions_generator import _find_list_page as _flp_client
                                _act_segment = _act_rel.split("/")[-2]  # "projects" depuis app/projects/actions.ts
                                _client_model = next(
                                    (m for m in (spec_obj.models if spec_obj else [])
                                     if _flp_client(m.name, spec_obj).lstrip("/") == _act_segment),
                                    None,
                                )
                                if _client_model:
                                    _types_abs = os.path.join(project_workdir, "lib", "types.ts")
                                    if os.path.exists(_types_abs):
                                        with open(_types_abs, "r", encoding="utf-8") as _tf:
                                            _types_content = _tf.read()
                                        _serial_key = f"export type Serialized{_client_model.name}"
                                        _t_start = _types_content.find(_serial_key)
                                        if _t_start >= 0:
                                            _t_end = _types_content.find("export type ", _t_start + len(_serial_key))
                                            _serial_type = _types_content[_t_start: _t_end if _t_end > _t_start else _t_start + 400].strip()
                                            _dep += (
                                                f"\n\nType disponible (CHAMPS EXACTS — ne pas inventer d'autres) :\n"
                                                f"```typescript\n{_serial_type}\n```"
                                            )
                            except Exception:
                                pass
                            break

                    # Injection du page_detail_hint pour ce page-client
                    if spec_obj is not None:
                        try:
                            from agents.dev_prompts import get_page_detail_hint
                            _page_route = "/" + "/".join(_path.split("/")[1:-1])  # app/{...}/page-client.tsx → /{...}
                            _page_route = _page_route.replace("/page-client", "")
                            _detail_hint = get_page_detail_hint(spec_obj, _page_route)
                            if _detail_hint:
                                _dep += f"\n\n{_detail_hint}"
                        except Exception:
                            pass

                elif _role == "page":
                    _seg = _path.split("/")[-2] if _path.count("/") >= 2 else ""
                    if _seg:
                        # Utilise _find_list_page (même logique que l'actions generator) pour
                        # retrouver le modèle dont la list_page correspond à ce segment d'URL.
                        # Cela gère correctement company→/companies, leave→/leaves, etc.
                        try:
                            from agents.dev_actions_generator import _find_list_page as _flp_page
                            _page_model_match = next(
                                (m for m in (spec_obj.models if spec_obj else [])
                                 if _flp_page(m.name, spec_obj).lstrip("/") == _seg),
                                None,
                            )
                        except Exception:
                            _page_model_match = None
                        _sv_cands = (
                            [_pascal_to_kebab_local(_page_model_match.name)]
                            if _page_model_match else [_seg, _seg.rstrip("s")]
                        )
                        for _sv in _sv_cands:
                            _svc_abs = os.path.join(project_workdir, "lib", "services",
                                                    f"{_sv}.service.ts")
                            if os.path.exists(_svc_abs):
                                try:
                                    # Camelcase du service : "project" → "projectService"
                                    _svc_camel = _re_utils.sub(
                                        r"-(.)", lambda m: m.group(1).upper(), _sv
                                    ) + "Service"
                                    with open(_svc_abs, "r", encoding="utf-8") as _f:
                                        _dep = (
                                            f"\nlib/services/{_sv}.service.ts"
                                            f" (import : import {{ {_svc_camel} }} from '@/lib/services/{_sv}.service') :\n"
                                            f"```typescript\n{_f.read()[:400]}\n```"
                                        )
                                except Exception:
                                    pass
                                break
                    # F3 : page-client.tsx généré AVANT page.tsx (ordre inversé dans planner).
                    # Si page-client.tsx est sur disque, l'injecter pour que page.tsx passe
                    # les bonnes props — évite TS2741 (props required non passées).
                    _client_sibling = _path.replace("/page.tsx", "/page-client.tsx")
                    _client_sibling_abs = os.path.join(project_workdir, _client_sibling)
                    if os.path.exists(_client_sibling_abs):
                        try:
                            with open(_client_sibling_abs, "r", encoding="utf-8") as _cf:
                                _dep += (
                                    f"\npage-client.tsx (props à passer depuis ce Server Component) :\n"
                                    f"```typescript\n{_cf.read()[:500]}\n```"
                                )
                        except Exception:
                            pass
                    # Phase-Aware : injection du détail de cette page spécifiquement.
                    if spec_obj is not None:
                        try:
                            from agents.dev_prompts import get_page_detail_hint
                            _page_route = "/" + "/".join(_path.split("/")[1:-1])
                            _detail_hint = get_page_detail_hint(spec_obj, _page_route)
                            if _detail_hint:
                                _dep += f"\n\n{_detail_hint}"
                        except Exception:
                            pass

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
        result = await graph.ainvoke(initial_state, {"recursion_limit": 600})

        # ── Signal de succès unique : build_command_executed + build_exit_code == 0 ──
        # Phase B : on ne surcharge plus le résultat depuis .next/ sur disque.
        # .next/ est logué comme signal secondaire uniquement (détection d'anomalie).
        disk_next = _check_next_dir_on_disk()
        final_success = bool(result.get("success", False))
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
