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

import json
import logging
import operator
import os
import re
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
    last_counted_build_call_id: str  # evite de compter 2x le meme build echoue


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
    patterns = [
        r"\./?(app/[^\s:(]+\.tsx?)",   # ./app/xxx.tsx ou app/xxx.tsx
        r"\./?(lib/[^\s:(]+\.tsx?)",   # ./lib/xxx.ts
        r"\./?(pages/[^\s:(]+\.tsx?)", # ./pages/xxx.tsx (rare)
    ]
    for pat in patterns:
        m = re.search(pat, error)
        if m:
            return m.group(1)
    return None


CONTRACT_FILE = ".factory-contract.json"


def _page_file_for_route(route: str) -> str:
    """Route déclarée par l'architect → fichier page.tsx correspondant. '/' → app/page.tsx."""
    r = (route or "/").strip()
    if not r.startswith("/"):
        r = "/" + r
    return "app/page.tsx" if r == "/" else f"app{r.rstrip('/')}/page.tsx"


def write_contract_file(spec_obj, project_workdir: str, protected: set[str]) -> dict:
    """Écrit le contrat machine consommé par quality_check.mjs (règles C*).

    Le compilateur TypeScript ne voit que la syntaxe : un KPI qui agrège 20 lignes sur 500
    compile parfaitement. Ce contrat donne au checker l'intention déclarée par l'architect,
    seule référence permettant de dire que le code ment.

    Seules les pages ayant une entrée pages_detail y figurent — ce sont celles écrites par
    le LLM. Les pages déterministes (protégées) sont exclues : leurs garanties sont tenues
    par les générateurs, pas par un contrôle a posteriori.
    """
    pages: list[dict] = []
    pd_map = getattr(spec_obj, "pages_detail", {}) or {}

    for route, entry in pd_map.items():
        if not isinstance(entry, dict):
            continue
        page_file = _page_file_for_route(route)
        if page_file in protected:
            continue

        fetches = [f for f in (entry.get("data_fetches") or []) if isinstance(f, dict)]
        agg_sources = sorted({
            e["source"]
            for e in list(entry.get("kpis") or []) + list(entry.get("filtered_lists") or [])
            if isinstance(e, dict) and e.get("source")
        })
        pages.append({
            "file": page_file,
            "path": route,
            "data_fetches": [{"as": f.get("as", ""), "service": f.get("service", "")} for f in fetches],
            "agg_sources": agg_sources,
            "allows_data": bool(fetches),
        })

    contract = {
        "paginated_methods": ["getAll", "getAllWithRelations", "getPublicAll", "getPublished"],
        "pages": pages,
    }
    dest = os.path.join(project_workdir, CONTRACT_FILE)
    with open(dest, "w", encoding="utf-8") as fh:
        json.dump(contract, fh, ensure_ascii=False, indent=2)
    logger.info("[dev_graph] contrat qualité écrit : %d page(s) LLM sous contrat", len(pages))
    return contract


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
    # Crashs des générateurs déterministes cœur. Un générateur qui plante ne doit PAS
    # basculer en douce vers le LLM (Level A dégradé en improvisation, en silence) : on
    # collecte ici et on abandonne le run avant la génération LLM (voir _prebuild_errors).
    _generator_errors: list[str] = []
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
        # Validation structurelle immédiate — évite de découvrir le problème 5 min plus
        # tard au moment de `prisma generate` pendant le build Next.js.
        _schema_errors = []
        if "datasource db" not in schema_content:
            _schema_errors.append("bloc datasource db manquant")
        if "generator client" not in schema_content:
            _schema_errors.append("bloc generator client manquant")
        if schema_content.count("model ") < len(spec_obj.models):
            _schema_errors.append(
                f"{schema_content.count('model ')} blocs model générés pour "
                f"{len(spec_obj.models)} modèles attendus"
            )
        if schema_content.count("{") != schema_content.count("}"):
            _schema_errors.append("accolades non équilibrées dans schema.prisma")
        if _schema_errors:
            raise RuntimeError(f"schema.prisma invalide : {'; '.join(_schema_errors)}")
        logger.info(
            f"[dev_graph] schema.prisma matérialisé depuis ProjectSpec "
            f"({len(spec_obj.models)} modèles)"
        )
    except Exception as _se:
        logger.error(f"[dev_graph] schema.prisma FATAL : {_se}", exc_info=True)
        raise

    # ── Contextes modèles (calculés UNE SEULE FOIS, partagés par tous les générateurs) ─
    # ModelGenerationContext est la source unique de vérité pour la détection de champs,
    # les flags has_slug/has_status/has_public_pages, la résolution FK, etc.
    # Doit être calculé AVANT les générateurs de pages, types, schemas et services.
    _model_contexts: dict = {}
    _enriched_spec = None
    if spec_obj is not None:
        try:
            from .dev_model_context import build_all_contexts
            from agents.semantic_spec import EnrichedSpec as _EnrichedSpec
            _enriched_raw = spec.get("enriched_spec") or {}
            _enriched_spec = _EnrichedSpec(**_enriched_raw) if _enriched_raw else None
            _model_contexts = build_all_contexts(spec_obj, enriched_spec=_enriched_spec)
            logger.info(
                "[dev_graph] %d ModelGenerationContext calculés (enriched_spec=%s)",
                len(_model_contexts), bool(_enriched_spec),
            )
        except Exception as _mc_err:
            logger.error(f"[dev_graph] build_all_contexts FATAL : {_mc_err}", exc_info=True)
            raise RuntimeError(f"build_all_contexts failed: {_mc_err}") from _mc_err

    # ── Niveau 1 — Page Contract Calculator ─────────────────────────────────
    # Contrats navigation/données pour toutes les pages modèle.
    # Injectés dans _file_brief par executor_node (voir closure ci-dessous).
    # Distinct de _page_contracts (planner.py) qui couvre uniquement les pages
    # [INTERACTIVE] et injecte des hints service dans context_hint du plan.
    _page_nav_contracts: dict = {}
    if spec_obj is not None and _model_contexts:
        try:
            from .dev_page_contract import compute_page_contracts as _compute_contracts
            _page_nav_contracts = _compute_contracts(spec_obj, _model_contexts)
        except Exception as _pc_err:
            logger.warning("[dev_graph] page_contract non bloquant : %s", _pc_err)

    # ══ FONDATIONS — générés avant tout fichier UI ════════════════════════════
    # Ordre correct : types → schemas → services → actions → pages → page-clients
    # Les pages et page-clients importent ces fichiers — ils doivent exister sur
    # le disque avant que le compilateur TypeScript les référence au build.

    # ── Génération déterministe : lib/types.ts ───────────────────────
    # BLOQUANT : les page stubs importent @/lib/types. Si ce fichier est absent,
    # le LLM invente ses propres interfaces → types incorrects → erreurs TS silencieuses.
    if spec_obj is not None:
        try:
            from .dev_types_generator import generate_types_file
            _types_result = generate_types_file(spec_obj, project_workdir, contexts=_model_contexts or None)
            template_written[_types_result.path] = _types_result.content
            logger.info("[dev_graph] lib/types.ts généré de manière déterministe")
        except Exception as _tg_err:
            _template_error = f"TYPES_GENERATOR_FAILED: {_tg_err}"
            logger.error(f"[dev_graph] {_template_error}")

    # ── Génération déterministe : lib/schemas.ts ─────────────────────
    # BLOQUANT : les Server Actions importent les schemas Zod pour valider les inputs.
    if spec_obj is not None and not _template_error:
        try:
            from .dev_zod_generator import generate_schemas_file
            _schemas_result = generate_schemas_file(spec_obj, project_workdir, contexts=_model_contexts or None)
            if _schemas_result:
                template_written[_schemas_result.path] = _schemas_result.content
                logger.info("[dev_graph] lib/schemas.ts généré de manière déterministe")
        except Exception as _zg_err:
            _template_error = f"ZOD_GENERATOR_FAILED: {_zg_err}"
            logger.error(f"[dev_graph] {_template_error}")

    # ── Génération déterministe : lib/services/*.ts ───────────────────
    if spec_obj is not None:
        try:
            from .dev_service_generator import generate_service_files
            _svc_written = generate_service_files(spec_obj, project_workdir, contexts=_model_contexts or None, enriched_spec=_enriched_spec)
            template_written.update(_svc_written)
            logger.info("[dev_graph] %d services DAL générés de manière déterministe", len(_svc_written))
        except Exception as _svc_err:
            _generator_errors.append(f"SERVICE_GENERATOR_FAILED: {_svc_err}")
            logger.error("[dev_graph] service generator a échoué (bloquant) : %s", _svc_err)

    # ── Génération déterministe : prisma/seed.ts (Preview local, dev-only) ──
    # Données de démonstration. Exclu du build (tsconfig) → un bug de seed ne casse
    # jamais l'app. Non bloquant : une erreur ici n'empêche pas la génération.
    if spec_obj is not None and _model_contexts:
        try:
            from .dev_seed_generator import generate_seed_file
            _seed_written = generate_seed_file(spec_obj, project_workdir, contexts=_model_contexts)
            template_written.update(_seed_written)
            logger.info("[dev_graph] prisma/seed.ts généré (%d modèle(s))", len(_model_contexts))
        except Exception as _seed_err:
            logger.warning("[dev_graph] seed generator échoué (non bloquant) : %s", _seed_err)

    # ── Génération déterministe : app/**/actions.ts ───────────────────
    if spec_obj is not None:
        try:
            from .dev_actions_generator import generate_action_files
            _act_written = generate_action_files(spec_obj, project_workdir, model_contexts=_model_contexts or None)
            template_written.update(_act_written)
            logger.info("[dev_graph] %d fichiers actions.ts générés de manière déterministe", len(_act_written))
        except Exception as _act_err:
            _generator_errors.append(f"ACTIONS_GENERATOR_FAILED: {_act_err}")
            logger.error("[dev_graph] actions generator a échoué (bloquant) : %s", _act_err)

    # ══ UI INFRASTRUCTURE — design system, layout, navigation ════════════════════
    # Générés avant les pages pour que les composants UI existent sur disque
    # quand le LLM démarre. Tous lockés dans template_written.
    _design_system = spec.get("design_system") or getattr(spec_obj, "design_system", {}) or {}

    # ── Design system : composants UI + tailwind.config.js + globals.css ─────
    if spec_obj is not None:
        try:
            from .dev_design_system_generator import generate_design_system
            _ds_files = generate_design_system(project_workdir, design_system=_design_system)
            template_written.update(_ds_files)
            logger.info("[dev_graph] design system généré (%d fichiers, primary=%s)",
                        len(_ds_files), _design_system.get("primary_color", "blue-600"))
        except Exception as _ds_err:
            logger.warning("[dev_graph] design_system_generator non bloquant : %s", _ds_err)

    # ── Layout + DashboardShell — avec les vraies couleurs du brief ───────────
    if spec_obj is not None:
        try:
            from .dev_layout_generator import generate_layout
            _layout_files = generate_layout(project_workdir, project_name, spec, spec_obj=spec_obj, enriched_spec=_enriched_spec)
            template_written.update(_layout_files)
            logger.info("[dev_graph] layout shell généré (layout_type=%s, sidebar_bg=%s)",
                        _design_system.get("layout_type", "sidebar"),
                        _design_system.get("sidebar_bg", "white"))
        except Exception as _ly_err:
            logger.warning("[dev_graph] layout_generator non bloquant : %s", _ly_err)

    # ══ UI — générés après les fondations ═════════════════════════════════════

    # ── Génération déterministe : pages + loading + error ───────────────────────
    # generate_page_stubs : page.tsx entièrement déterministe pour les pages avec
    #   champ `model` → ajouté à template_written (LLM ne peut pas écraser).
    #   Pour les pages sans `model` : stub auth-guard minimal (LLM peut compléter).
    if spec_obj is not None:
        try:
            from .dev_pages_generator import (
                generate_loading_files,
                generate_error_files,
                generate_root_page_if_needed,
                generate_page_stubs,
                generate_edit_page_stubs,
            )
            from .dev_middleware_generator import generate_middleware

            # Middleware dynamique : routes publiques injectées depuis spec.get_public_pages()
            _mw_files = generate_middleware(spec_obj, project_workdir)
            template_written.update(_mw_files)

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
            _page_files = generate_page_stubs(spec_obj, project_workdir, contexts=_model_contexts or None)
            template_written.update(_page_files)

            # Pages edit déterministes (update form) pour les modèles avec intent CRUD.
            _edit_stubs = generate_edit_page_stubs(spec_obj, project_workdir, contexts=_model_contexts or None)
            template_written.update(_edit_stubs)

            generate_loading_files(spec_obj, project_workdir)
            generate_error_files(spec_obj, project_workdir)
        except Exception as _pg_err:
            _generator_errors.append(f"PAGE_GENERATOR_FAILED: {_pg_err}")
            logger.error("[dev_graph] page generators ont échoué (bloquant) : %s", _pg_err)

    # ── Génération déterministe : SEO (sitemap.ts + robots.ts) ────────────────
    # Sprint 5 (Type D-complet) — uniquement si l'app a des pages publiques.
    # Le generateMetadata des pages detail-slug publiques est émis par _gen_page_full.
    if spec_obj is not None:
        try:
            from .dev_seo_generator import generate_seo_files
            _seo_files = generate_seo_files(spec_obj, _model_contexts or {}, project_workdir)
            template_written.update(_seo_files)
            if _seo_files:
                logger.info("[dev_graph] %d fichiers SEO générés : %s", len(_seo_files), list(_seo_files.keys()))
        except Exception as _seo_err:
            logger.warning(f"[dev_graph] seo generator non bloquant : {_seo_err}")

    # ── Génération déterministe : page-client.tsx (Level A) ──────────────────
    # Tous les page-client.tsx CRUD standard sont maintenant déterministes :
    # list (table Tailwind), create (form + FK selects), edit (form + defaultValues), detail.
    # Ces fichiers sont ajoutés à template_written → le LLM ne peut pas les écraser.
    # Les page-client.tsx custom (dashboard, hub, etc.) restent au LLM (Level B).
    if spec_obj is not None and _model_contexts:
        try:
            from .dev_form_generator import generate_all_page_clients
            _form_files = generate_all_page_clients(spec_obj, _model_contexts, project_workdir, enriched_spec=_enriched_spec, design_system=_design_system)
            template_written.update(_form_files)
            logger.info("[dev_graph] %d page-client.tsx générés de manière déterministe", len(_form_files))
        except Exception as _fg_err:
            _generator_errors.append(f"FORM_GENERATOR_FAILED: {_fg_err}")
            logger.error("[dev_graph] form generator a échoué (bloquant) : %s", _fg_err)

    # ── Génération déterministe : pages détail parent auto-manquantes ───────────
    # Pour chaque modèle parent (référencé via FK par un enfant CROSS_ENTITY) qui n'a
    # PAS de page détail déclarée dans le spec, on génère app/{list}/[id]/page.tsx +
    # page-client.tsx — résout les 404 post-création d'enfants (ex: createComment →
    # redirect(`/tasks/${validated.taskId}`) → 404 si /tasks/[id] absent).
    if spec_obj is not None and _model_contexts:
        try:
            from .dev_form_generator import generate_parent_detail_pages
            _parent_detail_files = generate_parent_detail_pages(spec_obj, _model_contexts, project_workdir, design_system=_design_system)
            template_written.update(_parent_detail_files)
            if _parent_detail_files:
                logger.info("[dev_graph] %d fichier(s) parent detail auto-générés", len(_parent_detail_files))
        except Exception as _pd_err:
            _generator_errors.append(f"PARENT_DETAIL_GENERATOR_FAILED: {_pd_err}")
            logger.error("[dev_graph] parent detail pages ont échoué (bloquant) : %s", _pd_err)

    # Les pages détail parent+enfants sont gérées structurellement :
    # - page.tsx : déterministe via generate_page_stubs (flux normal, model présent)
    # - page-client.tsx : déterministe via module_detail_with_children
    #   (détection via ctx.relation_fields dans dev_form_generator — pas de marqueurs texte)
    # Aucun check textuel pages_detail nécessaire ici.

    # ── Hub page déterministe : app/dashboard/page.tsx ────────────────────────
    # Le LLM oublie régulièrement `import Link from 'next/link'` sur cette page → build fail.
    # La hub page est entièrement dérivable du spec_obj → on la génère avant le LLM.
    if spec_obj is not None and _model_contexts:
        try:
            from .dev_hub_generator import generate_hub_page as _gen_hub
            _hub_files = _gen_hub(spec_obj, _model_contexts, project_workdir, pages_detail=getattr(spec_obj, "pages_detail", {}) or {})
            template_written.update(_hub_files)
        except Exception as _hub_err:
            _generator_errors.append(f"HUB_GENERATOR_FAILED: {_hub_err}")
            logger.error("[dev_graph] hub_generator a échoué (bloquant) : %s", _hub_err)

    # ── Home publique déterministe : app/page.tsx avec liste filtrée ──────────
    # Cas club : « / » public montre « prochaines sorties » (liste filtrée). Le LLM l'écrivait
    # paginé + non filtré (C1). Patron 3a appliqué au public : fetch dé-paginé + filtre compilé.
    # generate_root_page_if_needed a laissé « / » au LLM (data_fetches présents) ; on comble ici.
    if spec_obj is not None and _model_contexts:
        try:
            from .dev_hub_generator import generate_public_home as _gen_home
            _home_files = _gen_home(spec_obj, _model_contexts, project_workdir, pages_detail=getattr(spec_obj, "pages_detail", {}) or {})
            template_written.update(_home_files)
        except Exception as _home_err:
            _generator_errors.append(f"PUBLIC_HOME_GENERATOR_FAILED: {_home_err}")
            logger.error("[dev_graph] public home generator a échoué (bloquant) : %s", _home_err)

    # ── Feature modules (registry déclaratif depuis stack JSON config) ───────
    if spec_obj is not None and _model_contexts:
        try:
            from .feature_module import load_feature_modules, run_feature_modules
            _fm_names = stack_cfg.get("feature_modules", [])
            load_feature_modules(_fm_names, package=__name__.rsplit(".", 1)[0])
            _feature_files = run_feature_modules(spec_obj, _model_contexts, _enriched_spec, project_workdir, design_system=_design_system)
            template_written.update(_feature_files)
            if _feature_files:
                logger.info("[dev_graph] %d fichier(s) de feature modules", len(_feature_files))
        except Exception as _fm_err:
            _generator_errors.append(f"FEATURE_MODULES_FAILED: {_fm_err}")
            logger.error("[dev_graph] feature_modules ont échoué (bloquant) : %s", _fm_err)

    # ── Guard pré-build : cohérence page.tsx → page-client.tsx ─────────────
    # Après tous les générateurs déterministes, vérifie que chaque page.tsx
    # qui importe './page-client' a son page-client.tsx dans template_written.
    # Si absent → GENERATION_ERROR avant même que le LLM démarre.
    # Cible : détecter les bugs générateur tôt (TS2307 "Cannot find module") plutôt
    # qu'après le build Next.js (~5 min plus tard).
    # Seed avec les crashs de générateurs cœur (+ types/zod) : un générateur qui a planté
    # doit abandonner le run ici, jamais laisser le LLM improviser le fichier manquant.
    _prebuild_errors: list[str] = list(_generator_errors)
    if _template_error:
        _prebuild_errors.append(_template_error)
    _page_client_import_re = re.compile(r"['\"]\.\/page-client['\"]")
    for _tw_path, _tw_content in list(template_written.items()):
        if not _tw_path.endswith("page.tsx"):
            continue
        if not _page_client_import_re.search(_tw_content):
            continue
        _client_path = _tw_path[: -len("page.tsx")] + "page-client.tsx"
        if _client_path not in template_written:
            _prebuild_errors.append(
                f"GENERATION_ERROR: {_tw_path} importe './page-client' "
                f"mais {_client_path} absent de template_written — "
                "corriger le générateur Python correspondant."
            )
            logger.error("[dev_graph] %s", _prebuild_errors[-1])

    if _prebuild_errors:
        logger.error(
            "[dev_graph] %d erreur(s) de cohérence pré-build — run annulé",
            len(_prebuild_errors),
        )
        _dev_tools_module.set_protected_files(None)
        _dev_tools_module.set_workdir(None)
        return {  # type: ignore[return-value]
            "messages": [], "spec": spec, "project_name": project_name, "run_id": run_id,
            "build_attempts": 0, "last_build_error": "\n".join(_prebuild_errors),
            "success": False, "build_command_executed": False,
            "build_exit_code": -1, "validated_files": [],
            "generation_turns": 0, "file_plan": None,
        }

    # ── Guard qualité spec : create implique edit ────────────────────────────
    # RÈGLE 7 (architect) : tout modèle avec une page create doit avoir une page edit.
    # Ce guard détecte les cas où l'architect a ignoré cette règle.
    # Niveau : WARNING (non bloquant) — l'app buildera mais sera incomplète fonctionnellement.
    if spec_obj is not None:
        _create_models: set[str] = set()
        _edit_models: set[str] = set()
        for _sp in getattr(spec_obj, "pages", []) or []:
            _pt = getattr(_sp, "page_type", "") or ""
            _pm = getattr(_sp, "model", None)
            if not _pm:
                continue
            if _pt == "create":
                _create_models.add(_pm)
            if _pt == "edit":
                _edit_models.add(_pm)
        for _missing_edit in _create_models - _edit_models:
            logger.warning(
                "[dev_graph] SPEC_WARNING: modèle '%s' a une page create mais pas de page edit — "
                "l'utilisateur ne pourra pas modifier ses entrées. "
                "Vérifier les RÈGLES DEDUCTION 7 dans l'architect.",
                _missing_edit,
            )

    # ── Guard qualité middleware : pas de wildcard parent sur routes mixtes ──
    # Détecte le pattern dangereux /recipes(.*) qui rend public /recipes/new.
    # Après le fix du middleware generator, ce guard est une protection contre régression.
    # Niveau : WARNING (non bloquant).
    _mw_content = template_written.get("middleware.ts", "")
    if _mw_content:
        # /(api|trpc) est le matcher standard de config.matcher (boilerplate Next.js),
        # PAS une route publique. Sans cette exclusion, le guard criait au loup à CHAQUE
        # run → on finissait par ignorer tous les warnings.
        _wildcard_re = re.compile(r"'(/[^']+)\(\.\*\)'")
        for _wc_match in _wildcard_re.findall(_mw_content):
            if _wc_match not in ("/sign-in", "/sign-up", "/(api|trpc)"):
                logger.warning(
                    "[dev_graph] MIDDLEWARE_WARNING: pattern wildcard '%s(.*)' dans middleware.ts — "
                    "peut rendre publics des sous-chemins auth=true (ex: /recipes/new). "
                    "Préférer les chemins exacts par page.",
                    _wc_match,
                )

    # Source de vérité unique : tout fichier pré-généré (template_written) est protégé.
    # protected_files du JSON config étend cette liste pour les cas limites (fichiers
    # protégés mais non pré-générés). Les deux sont fusionnés — plus de double gestion.
    _protected = set(template_written.keys()) | set(stack_cfg.get("protected_files", [
        "lib/prisma.ts", "prisma.config.ts", "prisma/schema.prisma", ".eslintrc.stack.json",
    ]))
    _dev_tools_module.set_protected_files(_protected)

    # Contrat machine pour le quality checker : ce que l'architect a déclaré, page par page.
    # Le build ne voit que la syntaxe ; ce fichier permet au checker de comparer le code
    # généré à l'intention (KPI tronqué par la pagination, fetch sur une page sans données).
    if spec_obj is not None:
        write_contract_file(spec_obj, project_workdir, _protected)

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
            # Passer _model_contexts évite de recalculer build_all_contexts une seconde fois.
            _service_map_str = format_service_map_for_prompt(spec_obj, contexts=_model_contexts or None)
            logger.info("[dev_graph] Service map calculé (%d modèles)", len(spec_obj.models))
        except Exception as _sg_err:
            logger.warning(f"[dev_graph] service map non bloquant : {_sg_err}")

    # ── LevelAManifest — contrat structuré Level A → dev_test ────────
    # Assemblé UNE SEULE FOIS après tous les générateurs déterministes.
    # Expose models (méthodes typées), template_written, page_contracts, service_map_str.
    # Consommé par planner_node (page_contracts) et executor_node (dep page service lookup).
    _level_a_manifest = None
    if spec_obj is not None and _model_contexts:
        try:
            from .level_a_manifest import (
                build_level_a_manifest as _build_manifest,
                generate_contract_md as _gen_contract,
            )
            from agents.planner import build_page_contracts as _bpc
            _page_contracts = _bpc(spec_obj, _model_contexts)
            _level_a_manifest = _build_manifest(
                spec_obj,
                _model_contexts,
                template_written,
                _service_map_str,
                page_contracts=_page_contracts,
            )
            # Génère CONTRACTS.md — référence méthodes Level A pour l'executor LLM
            _contract_md = _gen_contract(_level_a_manifest)
            _contract_path = os.path.join(project_workdir, "CONTRACTS.md")
            with open(_contract_path, "w", encoding="utf-8") as _cf:
                _cf.write(_contract_md)
            template_written["CONTRACTS.md"] = _contract_md
            logger.info(
                "[dev_graph] LevelAManifest assemblé : %d modèles, %d contrats de pages",
                len(_level_a_manifest.models), len(_level_a_manifest.page_contracts),
            )
        except Exception as _me:
            logger.warning("[dev_graph] LevelAManifest non bloquant : %s", _me)

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

    # ── Design Brief Generator (Sprint B) ───────────────────────────
    # 1 appel LLM → JSON de décisions visuelles par entité (icônes, badges, layout).
    # Placé ICI (après prisma generate) pour que les types Prisma soient disponibles
    # si le Page Enricher (Sprint C) doit vérifier TSC après enrichissement.
    _design_brief: dict = {}
    if spec_obj is not None and _prev_cmd_ok:
        try:
            import json as _json_db
            from .dev_design_brief import generate_design_brief as _gen_brief
            _design_brief = await _gen_brief(spec_obj, _enriched_spec, _design_system, project_workdir)
            if _design_brief:
                _brief_json = _json_db.dumps(_design_brief, ensure_ascii=False, indent=2)
                template_written["DESIGN_BRIEF.json"] = _brief_json
                logger.info("[dev_graph] DESIGN_BRIEF.json généré (%d entités)",
                            len(_design_brief.get("entities", {})))
        except Exception as _db_err:
            logger.warning("[dev_graph] design_brief non bloquant : %s", _db_err)

    # ── Shell Enricher (Phase 4.1) ───────────────────────────────────
    # Injecte les icônes Lucide dans DashboardShell/TopNavShell depuis nav_icons du design_brief.
    # Doit tourner APRÈS design_brief (qui écrit DESIGN_BRIEF.json) et AVANT page_enricher.
    # TSC guard intégré — rollback si TypeScript échoue.
    if spec_obj is not None and _design_brief and _prev_cmd_ok:
        try:
            from .dev_shell_enricher import enrich_shell_with_nav_icons as _enrich_shell
            await _enrich_shell(_design_brief, _design_system, project_workdir, template_written)
        except Exception as _se_err:
            logger.warning("[dev_graph] shell_enricher non bloquant : %s", _se_err)

    # ── Enrichissement visuel DÉTERMINISTE (remplace le Page Enricher LLM) ────────
    # L'ancien Page Enricher LLM (Sprint C) réécrivait le fichier ENTIER pour appliquer le
    # design brief → dérive systématique (classes Tailwind dynamiques purgées → badges sans
    # couleur, colonnes fantômes). Générer ≠ éditer : un LLM qui ré-émet tout le fichier
    # régénère et invente, il ne « touche pas juste 3 endroits ». Le design brief étant un
    # vocabulaire FERMÉ (icône/badges/highlights/layout), il se COMPILE de façon déterministe :
    # on re-génère les page-clients avec design_brief → le Design Compiler injecte les
    # décorations en classes STATIQUES dans les templates. Fiable, et le design vit désormais
    # en amont (partagé), plus dans une passe de réécriture post-hoc.
    if spec_obj is not None and _design_brief and _model_contexts:
        try:
            from .dev_form_generator import generate_all_page_clients as _regen
            _decorated = _regen(
                spec_obj, _model_contexts, project_workdir,
                enriched_spec=_enriched_spec, design_system=_design_system,
                design_brief=_design_brief,
            )
            template_written.update(_decorated)
            _protected.update(_decorated.keys())
            logger.info("[dev_graph] enrichissement visuel déterministe : %d page-client(s) décoré(s)",
                        len(_decorated))
        except Exception as _pe_err:
            logger.warning("[dev_graph] enrichissement visuel non bloquant : %s", _pe_err)

    # Protéger lib/ (types, schemas, services) + app/**/actions.ts contre réécriture LLM.
    _protected.update(
        k for k in template_written
        if k.startswith("lib/")
        or k.endswith("/actions.ts")
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
                design_system=_design_system,
            )
            logger.info("[dev_graph] System prompt chargé depuis dev_prompts.py")
        except Exception as e:
            logger.error(f"[dev_graph] build_system_prompt() FAILED — run annulé : {e}")
            raise RuntimeError(f"SYSTEM_PROMPT_BUILD_FAILED: {e}") from e

    # ── Outils ───────────────────────────────────────────────────────
    tools = list(DEV_TOOLS) + [web_search]

    logger.info(f"[dev_graph] {len(tools)} outils : {[t.name for t in tools]}")

    # ── Règles de rôle depuis la config stack (SSoT) ─────────────────
    # code_role_hints dans nextjs-clerk-prisma.json — chaque valeur est une liste de strings.
    _hints_raw = stack_cfg.get("code_role_hints", {})
    _role_rules_from_config: dict[str, str] = {
        role: "\n".join(lines) for role, lines in _hints_raw.items()
    } if _hints_raw else {}

    try:
        from agents.stack_config import get_llm_models as _get_llm_models
        _stack_dev_model = _get_llm_models(stack_id).get("dev", "gpt-4o-mini")
    except Exception:
        _stack_dev_model = "gpt-4o-mini"
    _dev_model = os.getenv("DEV_MODEL", os.getenv("OPENAI_MODEL", _stack_dev_model))
    _dev_api_key = os.getenv("DEV_API_KEY", os.getenv("OPENAI_API_KEY"))
    _dev_base_url = os.getenv("DEV_BASE_URL") or os.getenv("OPENAI_BASE_URL") or None
    # seed=42 est spécifique OpenAI — Gemini et autres providers le rejettent
    _supports_seed = "googleapis" not in (_dev_base_url or "") and "groq" not in (_dev_base_url or "")
    llm = ChatOpenAI(
        model=_dev_model,
        temperature=0,
        max_retries=3,
        model_kwargs={"seed": 42} if _supports_seed else {},
        api_key=_dev_api_key,
        base_url=_dev_base_url,
    )
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
        _plan = make_deterministic_plan(_spec_local, _tpl, manifest=_level_a_manifest, contexts=_model_contexts)
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

            # Dépendances du fichier cassé — re-injectées à chaque tour de correction.
            # _prune_messages supprime les rounds anciens : les dépendances injectées lors
            # de la génération initiale peuvent être perdues dès le 2ème tour de correction.
            # build_role_context() les reconstitue depuis le disque, borné et sans regex.
            _deps_ctx = ""
            if _err_file:
                _err_entry = next((e for e in _plan if e["path"] == _err_file), None)
                if _err_entry and _err_entry.get("role"):
                    try:
                        from .dev_context import build_role_context as _brc_corr
                        _deps_ctx = _brc_corr(
                            _err_entry["role"], _err_file, spec_obj,
                            project_workdir, _service_map_str, cache=_rag_cache,
                            manifest=_level_a_manifest,
                        )
                    except Exception:
                        pass
                if not _deps_ctx:
                    # Fallback : fichier hors plan ou rôle absent — lib/types.ts couvre la
                    # majorité des TS2339 (propriétés inexistantes sur SerializedXxx).
                    try:
                        with open(os.path.join(project_workdir, "lib", "types.ts"), "r", encoding="utf-8") as _tf:
                            _types_content = _tf.read(1200)
                        if _types_content:
                            _deps_ctx = f"\nlib/types.ts (contrats réels) :\n```typescript\n{_types_content}\n```"
                    except Exception:
                        pass

            messages.append(HumanMessage(content=(
                f"ERREUR BUILD à corriger :\n{_err_excerpt}"
                f"{_file_ctx}"
                f"{_deps_ctx}\n"
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

                # Injection brief fonctionnel par fichier — pages custom uniquement.
                # Le LLM reçoit la description exacte de la page (depuis pages_detail)
                # et les user_flows correspondants au moment de générer ce fichier.
                _file_brief = ""
                if spec_obj and _role in ("page", "page_client"):
                    _rt = _path[3:] if _path.startswith("app") else _path
                    _rt = re.sub(r"/(page|page-client|loading|error)\.tsx?$", "", _rt)
                    _rt = "/" if not _rt else (_rt if _rt.startswith("/") else "/" + _rt)
                    _pd_map = getattr(spec_obj, "pages_detail", {}) or {}
                    _pd_entry = _pd_map.get(_rt)
                    if isinstance(_pd_entry, dict) and _pd_entry.get("description"):
                        _file_brief = f"\nEXIGENCES BRIEF POUR CETTE PAGE : {_pd_entry['description']}"

                        # Les KPIs et listes filtrées du dashboard sont désormais CALCULÉS
                        # de façon déterministe (dev_hub_generator) et écrits dans un fichier
                        # protégé — plus de prose « utilise EXACTEMENT ces expressions » que le
                        # LLM ignorait (cause de C1). Ici on ne guide plus que les pages custom
                        # non-dashboard : quels services appeler, dé-paginés si agrégés.
                        from .dev_hub_generator import unpaginate_call
                        _agg_sources = {
                            _e["source"]
                            for _e in list(_pd_entry.get("kpis", []) or []) + list(_pd_entry.get("filtered_lists", []) or [])
                            if isinstance(_e, dict) and _e.get("source")
                        }
                        _data_fetches = _pd_entry.get("data_fetches", [])
                        if _data_fetches and isinstance(_data_fetches, list):
                            _fetches_str = " | ".join(
                                f"{f.get('as', '?')}: "
                                + (unpaginate_call(f.get('service', '?')) if f.get('as') in _agg_sources else f.get('service', '?'))
                                for f in _data_fetches if isinstance(f, dict)
                            )
                            if _fetches_str:
                                _file_brief += f"\nAPPELS SERVICE : {_fetches_str}"

                        _page_flows = [f for f in (getattr(spec_obj, "user_flows", []) or []) if _rt in f]
                        if _page_flows:
                            _file_brief += "\nFLOWS : " + " | ".join(_page_flows[:2])

                    # ── Niveau 1 : injection contrat de page ─────────────────
                    # Données navigation déterministes : slug_field, detail_path,
                    # badge_fields, service_method — élimine toute la classe de
                    # bugs LLM liés aux liens et aux services (slug vs id, etc.).
                    if _page_nav_contracts and _role in ("page", "page_client"):
                        from .dev_page_contract import format_own_contract, format_nav_contracts
                        _own = _page_nav_contracts.get(_rt)
                        if _own:
                            # Page modèle en fallback LLM → son propre contrat
                            _file_brief += format_own_contract(_own)
                        else:
                            # Page custom (home, dashboard overview) →
                            # référence navigation de toutes les entités
                            _nav_ctx = (
                                "private"
                                if any(kw in _rt for kw in ("/dashboard", "/admin", "/manage"))
                                else "public"
                            )
                            _nav_block = format_nav_contracts(_page_nav_contracts, _nav_ctx)
                            if _nav_block:
                                _file_brief += _nav_block

                _rule = _role_rules_from_config.get(_role, "")
                _ctx = (
                    f"CONTEXTE : {_hint}{_file_brief}\n\nREGLE {_role.upper()} :\n{_rule}"
                    if _rule else f"CONTEXTE : {_hint}{_file_brief}"
                )

                # Dépendances disque + standard RAG ciblé sur ce rôle (dev_context.py).
                _dep = build_role_context(_role, _path, spec_obj, project_workdir, _service_map_str, cache=_rag_cache, manifest=_level_a_manifest)

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
                                f"\nEXEMPLE STRUCTURE SEULEMENT ({_example_path}) :\n"
                                f"```typescript\n{_example_content}\n```\n"
                                f"⚠️ Les règles OBLIGATOIRES du CONTEXTE ci-dessous ont priorité absolue sur cet exemple.\n"
                            )
                        except Exception:
                            pass

                messages.append(HumanMessage(content=(
                    f"{_example_anchor}{_dep}{_ctx}\n\n"
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
        found_call_id = ""

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
            found_call_id = call_id

            # Succès : exit code 0 — préfixe "OK\n" de shell_exec, point final
            if content.startswith("OK\n"):
                build_succeeded = True
                build_exit = 0
                break

            # Échec : préfixe "FAILED (exit N)" de shell_exec
            last_error = content[:3000]
            m = re.search(r"FAILED \(exit (\d+)\)", content)
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
                            found_call_id = call.get("id", "hardening")
                            build_exit = 1  # conservatif — pas de succès sans ToolMessage
                            logger.warning(
                                "[extract_error] build command dans AIMessage sans ToolMessage associé "
                                "— output manquant ou tronqué"
                            )
                    break

        # N'incrémenter build_attempts que si c'est un NOUVEAU build (tool_call_id different).
        # Evite de compter 3x le meme build echoue quand le LLM corrige des fichiers
        # sans relancer le build entre chaque cycle extract_error.
        prev_call_id = state.get("last_counted_build_call_id") or ""
        is_new_build = build_executed and (found_call_id != prev_call_id)
        new_attempts = int(state.get("build_attempts", 0) or 0) + (1 if is_new_build else 0)

        if build_executed and not is_new_build:
            logger.debug(
                "[extract_error] meme build ToolMessage (%s) — build_attempts non incrémenté",
                found_call_id,
            )

        return {
            "last_build_error": last_error,
            "success": build_succeeded,
            "build_command_executed": build_executed,
            "build_exit_code": build_exit,
            "build_attempts": new_attempts,
            "last_counted_build_call_id": found_call_id if is_new_build else prev_call_id,
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

        # plan_failed : file_plan is None = échec planner (distinct de [] = plan vide légitime).
        # Sortie immédiate — pas de retry LLM possible sans plan.
        if state.get("file_plan") is None:
            logger.error("[route_after_tools] file_plan is None (plan_failed) — arrêt immédiat")
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
            # Détection generator_bug : si l'erreur TSC est dans un fichier template_written,
            # le LLM ne peut pas le modifier — inutile de retenter, c'est un bug générateur.
            _err_file = _extract_error_file(last_error)
            if _err_file and _err_file in template_written:
                logger.error(
                    "[dev_graph] GENERATOR_BUG — erreur TSC dans fichier déterministe '%s' "
                    "(présent dans template_written). Le LLM ne peut pas corriger ce fichier. "
                    "Corriger le générateur Python correspondant.",
                    _err_file,
                )
                return END

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

    # ── Progressive Validation ────────────────────────────────────────
    # Intercalé entre tools et restore.
    # Détecte les fichiers .ts/.tsx écrits dans le dernier tour LLM.
    #
    # NOTE tsc désactivé (F1) : npx tsc --noEmit prend 20-60s par appel × N fichiers
    # = timeout Temporal garanti. Réactivation prévue en Sprint 4.9 avec une approche
    # fichier-par-fichier plus légère (tsc --isolatedModules sur le fichier seul).
    # Actif : E2 service method check (lecture + regex, < 10ms).
    def progressive_validation_node(state: DevState) -> dict:
        # Trouver les fichiers .ts/.tsx écrits dans le dernier tour LLM
        newly_written_ts: set[str] = set()
        for msg in reversed(state["messages"]):
            if not isinstance(msg, AIMessage):
                continue
            for call in (getattr(msg, "tool_calls", None) or []):
                if call.get("name") != "write_file":
                    continue
                args = call.get("args", {})
                path = (args.get("path", "") if isinstance(args, dict) else "") or ""
                if path.endswith((".ts", ".tsx")) and path not in template_written:
                    abs_p = os.path.join(project_workdir, path)
                    if os.path.exists(abs_p):
                        newly_written_ts.add(path)
            break  # uniquement le dernier AIMessage

        if not newly_written_ts:
            return {}

        # E2 — Service method existence check (non-bloquant — log GENERATION_WARNING)
        # Croise les appels xxxService.method() dans les fichiers écrits vs LevelAManifest.
        if _level_a_manifest is not None:
            for ts_path in newly_written_ts:
                abs_p = os.path.join(project_workdir, ts_path)
                try:
                    with open(abs_p, "r", encoding="utf-8") as _ef:
                        _content = _ef.read()
                    for _match in re.finditer(r"(\w+Service)\.(\w+)\(", _content):
                        _svc_var = _match.group(1)
                        _method = _match.group(2)
                        for _mi in _level_a_manifest.models:
                            if getattr(_mi, "service_var", "") == _svc_var:
                                _available = {
                                    getattr(m, "name", "") for m in getattr(_mi, "methods", [])
                                }
                                if _method not in _available:
                                    logger.warning(
                                        "[progressive_validation] GENERATION_WARNING: %s appelle "
                                        "%s.%s() absent du manifest. Disponibles: %s",
                                        ts_path, _svc_var, _method, sorted(_available),
                                    )
                                break
                except Exception:
                    pass

    # ── Restauration des fichiers template supprimés ──────────────────
    # Intercalé entre tools et extract_error.
    # Le LLM peut supprimer des fichiers template via shell_exec (rm, python -c, etc.).
    # Ce nœud restaure silencieusement tout fichier template_written manquant sur disque.
    # Guard 1 dans write_file bloque la réécriture mais pas la suppression — ce nœud
    # ferme la vulnérabilité résiduelle sans bloquer les commandes shell légitimes.
    def restore_protected_node(state: DevState) -> dict:
        restored: list[str] = []
        for rel_path, content in template_written.items():
            abs_p = os.path.join(project_workdir, rel_path.replace("/", os.sep))
            if not os.path.exists(abs_p):
                try:
                    os.makedirs(os.path.dirname(abs_p), exist_ok=True)
                    from pathlib import Path as _Path
                    _Path(abs_p).write_text(content, encoding="utf-8")
                    restored.append(rel_path)
                except Exception as _re:
                    logger.warning("[restore] échec restauration %s : %s", rel_path, _re)
        if restored:
            logger.warning("[restore] %d fichier(s) template restaurés : %s", len(restored), restored)
        return {}

    # ── Assemblage du graph ──────────────────────────────────────────
    builder = StateGraph(DevState)
    builder.add_node("planner", planner_node)
    builder.add_node("executor", executor_node)
    builder.add_node("tools", ToolNode(tools, handle_tool_errors=True))
    builder.add_node("progressive_validation", progressive_validation_node)
    builder.add_node("restore", restore_protected_node)
    builder.add_node("extract_error", extract_build_error_node)

    builder.add_edge(START, "planner")
    builder.add_edge("planner", "executor")
    builder.add_conditional_edges("executor", tools_condition, {
        "tools": "tools",
        "__end__": END,
    })
    builder.add_edge("tools", "progressive_validation")
    builder.add_edge("progressive_validation", "restore")
    builder.add_edge("restore", "extract_error")
    builder.add_conditional_edges("extract_error", route_after_tools, {
        "executor": "executor",
        END: END,
    })

    graph = builder.compile()

    # ── State initial ─────────────────────────────────────────────────
    spec_models = [m.get("name", "") for m in spec.get("models", [])]

    # Pages custom uniquement — celles que le LLM génère effectivement.
    # Les pages avec model (list/create/detail/edit) sont pré-générées déterministiquement
    # et dans template_written. Les lister ici confond le LLM sur son périmètre.
    spec_custom_pages = [
        p.get("path", "") for p in spec.get("pages", [])
        if p.get("page_type", "custom") == "custom" or not p.get("model")
    ]

    # Webhooks seulement — les routes CRUD sont des Server Actions.
    spec_webhooks = [
        f"{r.get('method','')} {r.get('path','')}"
        for r in spec.get("routes", [])
        if "webhook" in r.get("path", "").lower() or "stripe" in r.get("path", "").lower()
    ]

    # Injecter le design brief directement dans le HumanMessage pour les pages custom (home, dashboard).
    # Le LLM ne lit pas toujours DESIGN_BRIEF.json via read_file — l'injection garantit qu'il reçoit
    # les tokens visuels (primary_color, brand_name, density, animation_style) sans appel outil.
    _brief_hint = ""
    if _design_brief:
        import json as _json_hint
        _brief_compact = {
            k: v for k, v in _design_brief.items()
            if k in ("brand_name", "primary_color", "density", "animation_style", "entities", "nav_icons")
        }
        _brief_hint = (
            "\n\nDESIGN_BRIEF (déjà disponible — NE PAS appeler read_file pour ce fichier) :\n"
            + _json_hint.dumps(_brief_compact, ensure_ascii=False, indent=2)
            + "\nUtilise brand_name pour les titres/hero, primary_color pour les accents, "
            "density pour les paddings, animation_style pour framer-motion (si 'spring') ou transitions CSS."
        )

    initial_state: DevState = {
        "messages": [
            SystemMessage(content=system_prompt),
            HumanMessage(content=(
                f"Génère le projet '{project_name}'.\n\n"
                f"Modèles Prisma (déjà dans schema.prisma) : {spec_models}\n"
                f"Pages custom à générer (TON TRAVAIL) : {spec_custom_pages}\n"
                + (f"Webhooks (route.ts requis) : {spec_webhooks}\n" if spec_webhooks else "")
                + f"\nFingerprint spec : {spec.get('spec_fingerprint', 'n/a')}\n"
                "Toutes les pages avec model (list/create/detail/edit) sont PRÉ-GÉNÉRÉES "
                "et verrouillées. Consulte le plan pour la liste exacte des fichiers à créer."
                + _brief_hint
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
        "last_counted_build_call_id": "",
    }

    try:
        result = await graph.ainvoke(initial_state, {"recursion_limit": 100})

        final_success = bool(result.get("success", False))

        # ── Reconciliation build post-graph ──────────────────────────────────────
        # Si le graph s'est arrêté avec success=False (MAX_BUILD_ATTEMPTS atteint ou
        # hardening path), on vérifie si le code est désormais valide avec un dernier
        # build synchrone. Le LLM a peut-être corrigé les erreurs dans la dernière
        # itération sans avoir eu le temps de relancer le build.
        if not final_success:
            try:
                _recon_env = os.environ.copy()
                _recon_env["CI"] = "true"
                _recon_env.setdefault(
                    "DATABASE_URL", "postgresql://user:CHANGEME@localhost:5432/db_placeholder"
                )
                logger.info("[dev_graph] reconciliation — tsc --noEmit ...")
                _tsc_r = subprocess.run(
                    "npx tsc --noEmit",
                    shell=True, capture_output=True, text=True,
                    timeout=120, cwd=project_workdir, env=_recon_env,
                )
                if _tsc_r.returncode == 0:
                    logger.info("[dev_graph] reconciliation — tsc OK → npm run build ...")
                    _build_r = subprocess.run(
                        "npm run build",
                        shell=True, capture_output=True, text=True,
                        timeout=300, cwd=project_workdir, env=_recon_env,
                    )
                    if _build_r.returncode == 0:
                        final_success = True
                        result = dict(result)
                        result["success"] = True
                        result["build_exit_code"] = 0
                        result["build_command_executed"] = True
                        logger.info(
                            "[dev_graph] reconciliation build SUCCES — success override True"
                        )
                    else:
                        _bout = (_build_r.stdout + _build_r.stderr)[:600]
                        logger.warning(
                            "[dev_graph] reconciliation build FAILED (exit %d): %s",
                            _build_r.returncode, _bout,
                        )
                else:
                    _tout = (_tsc_r.stdout + _tsc_r.stderr)[:400]
                    logger.info("[dev_graph] reconciliation — tsc errors: %s", _tout)
            except Exception as _re:
                logger.warning("[dev_graph] reconciliation build exception: %s", _re)

        disk_next = _check_next_dir_on_disk()

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

        # ── Violations de contrat (C*) — BLOQUANTES ──────────────────────────────
        # Le build ne voit que la syntaxe. Les règles C* comparent le code au contrat
        # architect : un KPI tronqué par la pagination (C1) ou un fetch sur une page qui
        # doit rester statique (C2) COMPILE parfaitement, mais trahit l'intention.
        # On refuse le succès — sinon l'app "réussit" en mentant à l'utilisateur.
        _contract_blocked = False
        _blocking_violations = [
            v for v in quality_violations if str(v.get("rule", "")).startswith("C")
        ]
        if _blocking_violations and final_success:
            _contract_blocked = True
            final_success = False
            result["success"] = False
            _bundle = "\n".join(
                f"  [{v['rule']}] {v.get('file', '')}:{v.get('line', 0)} — {v.get('reason', '')}"
                for v in _blocking_violations
            )
            result["last_build_error"] = (
                "CONTRACT_VIOLATION — le code compile mais viole le contrat architect :\n"
                + _bundle
            )
            result["root_cause_category"] = "contract_violation"
            logger.error(
                "[dev_graph] CONTRACT_VIOLATION — %d violation(s) C* bloquante(s) : %s",
                len(_blocking_violations),
                [v["rule"] for v in _blocking_violations],
            )

        if disk_next and not final_success and not _contract_blocked:
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
