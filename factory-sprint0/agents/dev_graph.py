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

from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition

import agents.dev_tools as _dev_tools_module
from agents.dev_tools import write_file, read_file, list_directory, shell_exec, file_exists

logger = logging.getLogger(__name__)

MAX_BUILD_ATTEMPTS = 3
_BASE_WORKDIR = os.getenv("FACTORY_WORKDIR", "/app/generated-projects")

DEV_TOOLS = [write_file, read_file, list_directory, shell_exec, file_exists]


def _check_build_success_on_disk() -> bool:
    """Vérification déterministe : .next/ présent dans le workdir actif → build réussi."""
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


def _error_signature(stderr: str) -> str:
    """Hash stable des 200 premiers chars d'une erreur — détection de boucle."""
    return hashlib.md5(stderr[:200].encode()).hexdigest()[:8]


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
    _protected = {"lib/prisma.ts", "prisma.config.ts", "prisma/schema.prisma"}
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

    # ── Nœud Build Doctor ────────────────────────────────────────────
    async def build_doctor_node(state: DevState) -> dict:
        """Analyse l'erreur de build et injecte un diagnostic ciblé."""
        last_error = state.get("last_build_error", "")
        if not last_error:
            return {}

        build_attempts = state.get("build_attempts", 0) + 1
        logger.info(
            f"[build_doctor] Tentative {build_attempts}/{MAX_BUILD_ATTEMPTS} "
            f"| erreur: {last_error[:80]}..."
        )

        if build_attempts >= MAX_BUILD_ATTEMPTS:
            logger.warning("[build_doctor] MAX_BUILD_ATTEMPTS atteint — arrêt")
            return {"build_attempts": build_attempts}

        try:
            from agents.build_doctor import diagnose_build_error
            diagnosis = await diagnose_build_error(
                stderr=last_error,
                spec_dict=state.get("spec", {}),
            )
            return {
                "messages": [HumanMessage(content=diagnosis)],
                "build_attempts": build_attempts,
            }
        except Exception as e:
            logger.warning(f"[build_doctor] non bloquant : {e}")
            return {"build_attempts": build_attempts}

    # ── Extraction erreur + détection succès déterministe ────────────
    def extract_build_error_node(state: DevState) -> dict:
        """
        Parcourt les ToolMessages pour détecter :
        - un succès build déterministe (shell_exec OK + marqueurs next.js)
        - une erreur build à traiter
        """
        from langchain_core.messages import ToolMessage

        last_error = ""
        build_succeeded = False

        for msg in reversed(state["messages"]):
            if isinstance(msg, ToolMessage):
                content = str(getattr(msg, "content", "") or "")

                # Succès déterministe : shell_exec retourne "OK\n" + marqueurs next.js
                if content.startswith("OK\n") and any(marker in content for marker in [
                    "Creating an optimized production build",
                    "Compiled successfully",
                    "compiled successfully",
                    "Route (app)",
                    "✓ Compiled",
                ]):
                    build_succeeded = True
                    break

                # Erreur build
                if any(kw in content for kw in [
                    "Type error:", "Failed to compile", "Build failed",
                    "FAILED (exit", "error TS", "does not exist on type",
                    "Cannot find module", "SyntaxError",
                ]):
                    last_error = content[:3000]
                    break

        return {
            "last_build_error": last_error,
            "success": build_succeeded,
        }

    # ── Routage ──────────────────────────────────────────────────────
    def route_after_tools(state: DevState) -> str:
        last_error = state.get("last_build_error", "")
        build_attempts = state.get("build_attempts", 0)

        if state.get("success", False):
            return END
        if last_error and build_attempts < MAX_BUILD_ATTEMPTS:
            return "build_doctor"
        # MAX_BUILD_ATTEMPTS atteint avec erreur persistante → arrêt, pas de boucle
        if last_error and build_attempts >= MAX_BUILD_ATTEMPTS:
            return END
        return "dev"

    # ── Assemblage du graph ──────────────────────────────────────────
    builder = StateGraph(DevState)
    builder.add_node("dev", dev_node)
    builder.add_node("tools", ToolNode(tools, handle_tool_errors=True))
    builder.add_node("extract_error", extract_build_error_node)
    builder.add_node("build_doctor", build_doctor_node)

    builder.add_edge(START, "dev")
    builder.add_conditional_edges("dev", tools_condition)
    builder.add_edge("tools", "extract_error")
    builder.add_conditional_edges("extract_error", route_after_tools, {
        "build_doctor": "build_doctor",
        "dev": "dev",
        END: END,
    })
    builder.add_edge("build_doctor", "dev")

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
    }

    try:
        result = await graph.ainvoke(initial_state, {"recursion_limit": 80})

        # ── Vérification déterministe post-execution (.next/ sur disque) ──
        disk_success = _check_build_success_on_disk()
        if disk_success and not result.get("success"):
            logger.info("[dev_graph] Succès déterministe (.next/ présent) — override success=True")
            result = {**result, "success": True}
        elif not disk_success and result.get("success"):
            logger.warning("[dev_graph] .next/ absent malgré success=True — override success=False")
            result = {**result, "success": False}

        logger.info(
            f"[dev_graph] terminé — success={result.get('success')} "
            f"| build_attempts={result.get('build_attempts', 0)} "
            f"| .next/ présent={disk_success} "
            f"| workdir={project_workdir}"
        )
        return result
    finally:
        # Toujours réinitialiser — même en cas d'exception
        _dev_tools_module.set_protected_files(None)
        _dev_tools_module.set_workdir(None)
