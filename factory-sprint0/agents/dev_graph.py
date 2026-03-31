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

import hashlib
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

logger = logging.getLogger(__name__)

MAX_BUILD_ATTEMPTS = 3
MAX_PREBUILD_BLOCKS = 6
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
    error_signatures: List[str]
    build_command_executed: bool   # True ssi npm run build a été appelé et a retourné un exit code
    build_exit_code: int           # Exit code réel du dernier npm run build (0 = succès)
    prebuild_blocking: bool        # True si prebuild_pipeline bloque le build
    prebuild_report: dict          # Dernier prebuild_report sérialisé
    prebuild_block_count: int      # Nombre de blocages prebuild consécutifs


def _error_signature(stderr: str) -> str:
    """Hash stable des 200 premiers chars d'une erreur — détection de boucle."""
    return hashlib.md5(stderr[:200].encode()).hexdigest()[:8]


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
    # Cela évite que le LLM génère package.json avec du JSON double-encodé (EJSONPARSE).
    template_written: dict = {}
    try:
        from agents.dev_file_ops import write_template_files
        from agents.stack_config import load_stack_config
        stack_id = spec.get("stack_id", "") or "nextjs-clerk-prisma"
        stack_cfg = load_stack_config(stack_id)
        template_written = write_template_files(project_workdir, stack_cfg, project_name, stack_id)
        logger.info(
            f"[dev_graph] {len(template_written)} fichiers pré-générés depuis templates : "
            f"{list(template_written.keys())}"
        )
    except Exception as _te:
        logger.warning(f"[dev_graph] write_template_files non bloquant : {_te}")

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

    # Protéger les fichiers Prisma critiques contre réécriture LLM.
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
    # prisma generate est de l'infrastructure au même titre que npm install.
    # Le schema.prisma est déjà matérialisé depuis ProjectSpec — on génère
    # le client Prisma maintenant pour que les types @prisma/client soient
    # disponibles dès le premier fichier LLM. Non-bloquant si échec.
    try:
        logger.info(f"[dev_graph] prisma generate pre-run dans {project_workdir} ...")
        _prisma_result = subprocess.run(
            "npx prisma generate",
            shell=True,
            capture_output=True,
            text=True,
            cwd=project_workdir,
            timeout=120,
        )
        if _prisma_result.returncode == 0:
            logger.info("[dev_graph] prisma generate pre-run OK")
        else:
            logger.warning(
                f"[dev_graph] prisma generate pre-run FAILED (exit {_prisma_result.returncode}): "
                f"{(_prisma_result.stdout + _prisma_result.stderr)[:400]}"
            )
    except subprocess.TimeoutExpired:
        logger.warning("[dev_graph] prisma generate pre-run TIMEOUT (>120s)")
    except Exception as _pg_err:
        logger.warning(f"[dev_graph] prisma generate pre-run exception : {_pg_err}")

    # ── System prompt ────────────────────────────────────────────────
    if not system_prompt:
        try:
            from agents.dev_prompts import build_system_prompt
            if spec_obj is None:
                from agents.project_spec import ProjectSpec

                spec_obj = ProjectSpec(**spec)
            system_prompt = build_system_prompt(spec_obj, pre_written_files=list(template_written.keys()))
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
    tools = list(DEV_TOOLS)
    try:
        from agents.shared_tools import rag_search
        tools = tools + [rag_search]
    except Exception as _e:
        logger.warning(f"[dev_graph] rag_search non disponible : {_e}")

    logger.info(f"[dev_graph] {len(tools)} outils : {[t.name for t in tools]}")

    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, max_retries=3)
    llm_with_tools = llm.bind_tools(tools)

    # ── Nœud dev principal ───────────────────────────────────────────
    def dev_node(state: DevState) -> dict:
        messages = list(state["messages"])

        # Anti-loop : même erreur ≥ 2 fois → changement de stratégie obligatoire
        last_error = state.get("last_build_error", "")
        if last_error:
            sig = _error_signature(last_error)
            count = state.get("error_signatures", []).count(sig)
            if count >= 2:
                messages.append(HumanMessage(content=(
                    "⚠️ Tu as rencontré cette même erreur plusieurs fois sans la résoudre. "
                    "CHANGEMENT DE STRATÉGIE OBLIGATOIRE : "
                    "1. Utilise read_file pour lire le fichier exact mentionné dans l'erreur. "
                    "2. Identifie la ligne précise du problème. "
                    "3. Applique une correction ciblée sur ce fichier uniquement. "
                    "4. Appelle shell_exec(\"npx tsc --noEmit\") pour valider avant de rebuilder."
                )))

        response = llm_with_tools.invoke(messages)

        new_sigs = list(state.get("error_signatures", []))
        if last_error:
            new_sigs.append(_error_signature(last_error))

        return {
            "messages": [response],
            "error_signatures": new_sigs,
        }

    # ── Nœud Prebuild Gate (B.1b) ─────────────────────────────────────
    async def prebuild_gate_node(state: DevState) -> dict:
        """
        Intercepte les tool_calls avant exécution.
        Si un npm run build est demandé, exécute prebuild_pipeline:
        - blocking=True  -> injecte llm_correction_bundle et saute l'exécution tools
        - blocking=False -> autorise tools (donc build)
        """
        last_msg = state["messages"][-1] if state.get("messages") else None
        if not isinstance(last_msg, AIMessage):
            return {"prebuild_blocking": False}

        tool_calls = getattr(last_msg, "tool_calls", None) or []
        build_requested = False
        for call in tool_calls:
            name = str(call.get("name", "") or "")
            if not (name == "shell_exec" or name.endswith("shell_exec")):
                continue
            args = call.get("args", {})
            command = str(args.get("command", "") or "") if isinstance(args, dict) else str(args or "")
            if _is_build_command(command):
                build_requested = True
                break

        if not build_requested:
            return {"prebuild_blocking": False}

        try:
            from agents.prebuild_pipeline import (
                run_prebuild_pipeline, report_to_dict, PHASE_C_STAGES,
            )

            # PHASE_C_STAGES inclut ast_use_client — activé dès que _run_ast_use_client est implémenté.
            # Si tree-sitter absent → stage=skipped automatiquement (non bloquant).
            report = await run_prebuild_pipeline(
                project_dir=project_workdir,
                stack_id=str(spec.get("stack_id", "") or "nextjs-clerk-prisma"),
                run_id=run_id,
                project_name=project_name,
                stages=PHASE_C_STAGES,
            )
            report_dict = report_to_dict(report)
            if report.blocking:
                block_count = int(state.get("prebuild_block_count", 0) or 0) + 1
                bundle = report.llm_correction_bundle or (
                    "[PREBUILD_VIOLATIONS] Corrections obligatoires détectées avant build. "
                    "Corrige ces violations puis relance le build."
                )
                logger.warning(
                    "[prebuild] blocking=True — build bloqué (%d/%d), %d violation(s), stages_failed=%s",
                    block_count,
                    MAX_PREBUILD_BLOCKS,
                    len(report.violations),
                    report.stages_failed,
                )
                # OpenAI exige qu'un ToolMessage réponde à chaque tool_call_id de l'AIMessage.
                # Sans cela → HTTP 400 "tool_calls must be followed by tool messages".
                ack_ids: list[str] = []
                for call in tool_calls:
                    cid = str(call.get("id") or call.get("tool_call_id") or "").strip()
                    if cid:
                        ack_ids.append(cid)

                # Fallback robuste: certains providers/langchain conservent les ids bruts
                # dans additional_kwargs.tool_calls au lieu de state.tool_calls normalisé.
                raw_tool_calls = []
                if isinstance(getattr(last_msg, "additional_kwargs", None), dict):
                    raw_tool_calls = last_msg.additional_kwargs.get("tool_calls", []) or []
                for raw in raw_tool_calls:
                    if not isinstance(raw, dict):
                        continue
                    cid = str(raw.get("id") or "").strip()
                    if cid:
                        ack_ids.append(cid)

                # Dédupe en conservant l'ordre
                dedup_ids: list[str] = []
                seen_ids: set[str] = set()
                for cid in ack_ids:
                    if cid in seen_ids:
                        continue
                    seen_ids.add(cid)
                    dedup_ids.append(cid)

                tool_ack_messages = [
                    ToolMessage(
                        content="[PREBUILD_BLOCK] Build non exécuté — violations détectées. Attends les corrections.",
                        tool_call_id=cid,
                    )
                    for cid in dedup_ids
                ]
                logger.info(
                    "[prebuild] Tool acks envoyés: %d/%d",
                    len(tool_ack_messages),
                    len(tool_calls),
                )
                if block_count >= MAX_PREBUILD_BLOCKS:
                    logger.warning(
                        "[prebuild] max blocages atteint (%d) — arrêt pour éviter GraphRecursionError",
                        MAX_PREBUILD_BLOCKS,
                    )
                    hard_stop = (
                        "PREBUILD_BLOCK_LIMIT: même violation persistante après "
                        f"{MAX_PREBUILD_BLOCKS} corrections. "
                        "Arrêt du run pour éviter une boucle infinie."
                    )
                    return {
                        "messages": tool_ack_messages + [HumanMessage(content=bundle)],
                        "prebuild_blocking": True,
                        "prebuild_report": report_dict,
                        "prebuild_block_count": block_count,
                        "last_build_error": hard_stop,
                        "success": False,
                        "build_command_executed": False,
                        "build_exit_code": -1,
                    }
                return {
                    "messages": tool_ack_messages + [HumanMessage(content=bundle)],
                    "prebuild_blocking": True,
                    "prebuild_report": report_dict,
                    "prebuild_block_count": block_count,
                }

            logger.info(
                "[prebuild] blocking=False — build autorisé | stages_passed=%s",
                report.stages_passed,
            )
            return {
                "prebuild_blocking": False,
                "prebuild_report": report_dict,
                "prebuild_block_count": 0,
            }
        except Exception as e:
            logger.warning(f"[prebuild] pipeline non bloquant: {e}")
            return {"prebuild_blocking": False}

    # ── Extraction erreur + détection succès déterministe ────────────
    def extract_build_error_node(state: DevState) -> dict:
        """
        Parcourt les ToolMessages pour détecter :
        - un succès build (shell_exec exit 0 + marqueurs next.js — signal unique)
        - une erreur build à traiter

        Règle Phase B : success = npm run build exécuté + exit code 0.
        Aucun override basé sur présence de .next/ sur disque.
        """
        from langchain_core.messages import ToolMessage

        last_error = ""
        build_succeeded = False
        build_executed = False
        build_exit = -1

        for msg in reversed(state["messages"]):
            if isinstance(msg, ToolMessage):
                content = str(getattr(msg, "content", "") or "")

                # Succès build : shell_exec retourne "OK\n" + marqueurs next.js
                if content.startswith("OK\n") and any(marker in content for marker in [
                    "Creating an optimized production build",
                    "Compiled successfully",
                    "compiled successfully",
                    "Route (app)",
                    "✓ Compiled",
                ]):
                    build_succeeded = True
                    build_executed = True
                    build_exit = 0
                    break

                # Erreur build
                if any(kw in content for kw in [
                    "Type error:", "Failed to compile", "Build failed",
                    "FAILED (exit", "error TS", "does not exist on type",
                    "Cannot find module", "SyntaxError",
                ]):
                    last_error = content[:3000]
                    build_executed = True
                    # Extraire exit code si présent dans "FAILED (exit N)"
                    import re as _re
                    m = _re.search(r"exit\s+(\d+)", content)
                    build_exit = int(m.group(1)) if m else 1
                    break

        return {
            "last_build_error": last_error,
            "success": build_succeeded,
            "build_command_executed": build_executed,
            "build_exit_code": build_exit,
        }

    # ── Routage ──────────────────────────────────────────────────────
    def route_after_tools(state: DevState) -> str:
        last_error = state.get("last_build_error", "")

        if state.get("success", False):
            return END
        if last_error:
            return END
        return "dev"

    def route_from_dev(state: DevState) -> str:
        """Routage standard tools_condition, avec passage obligatoire par prebuild_gate."""
        decision = tools_condition(state)
        return "prebuild_gate" if decision == "tools" else "__end__"

    def route_after_prebuild(state: DevState) -> str:
        """Si prebuild bloque, retour au LLM sans exécuter les tool_calls."""
        if state.get("prebuild_blocking", False):
            if int(state.get("prebuild_block_count", 0) or 0) >= MAX_PREBUILD_BLOCKS:
                return "__end__"
            return "dev"
        return "tools"

    # ── Assemblage du graph ──────────────────────────────────────────
    builder = StateGraph(DevState)
    builder.add_node("dev", dev_node)
    builder.add_node("prebuild_gate", prebuild_gate_node)
    builder.add_node("tools", ToolNode(tools, handle_tool_errors=True))
    builder.add_node("extract_error", extract_build_error_node)

    builder.add_edge(START, "dev")
    builder.add_conditional_edges("dev", route_from_dev, {
        "prebuild_gate": "prebuild_gate",
        "__end__": END,
    })
    builder.add_conditional_edges("prebuild_gate", route_after_prebuild, {
        "tools": "tools",
        "dev": "dev",
        "__end__": END,
    })
    builder.add_edge("tools", "extract_error")
    builder.add_conditional_edges("extract_error", route_after_tools, {
        "dev": "dev",
        END: END,
    })

    graph = builder.compile()

    # ── State initial ─────────────────────────────────────────────────
    spec_models = [m.get("name", "") for m in spec.get("models", [])]
    spec_pages = [p.get("path", "") for p in spec.get("pages", [])]
    spec_routes = [f"{r.get('method','')} {r.get('path','')}" for r in spec.get("routes", [])]

    initial_state: DevState = {
        "messages": [
            SystemMessage(content=system_prompt),
            HumanMessage(content=(
                f"Génère le projet '{project_name}'.\n\n"
                f"Modèles Prisma : {spec_models}\n"
                f"Pages : {spec_pages}\n"
                f"Routes API : {spec_routes}\n\n"
                f"Fingerprint spec : {spec.get('spec_fingerprint', 'n/a')}\n"
                f"Suis le workflow du system prompt."
            )),
            *([HumanMessage(content=extra_feedback)] if extra_feedback else []),
        ],
        "spec": spec,
        "project_name": project_name,
        "run_id": run_id,
        "build_attempts": 0,
        "last_build_error": "",
        "success": False,
        "error_signatures": [],
        "build_command_executed": False,
        "build_exit_code": -1,
        "prebuild_blocking": False,
        "prebuild_report": {},
        "prebuild_block_count": 0,
    }

    try:
        result = await graph.ainvoke(initial_state, {"recursion_limit": 80})

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
