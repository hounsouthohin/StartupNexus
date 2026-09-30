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

    # ── Génération déterministe du cœur ──────────────────────────────
    # Toute la séquence des générateurs (templates → schema → contextes → types → schemas
    # → services → seed → actions → oracle → design system → layout → pages → SEO →
    # page-clients → hub → feature modules → garde pré-build) vit dans dev_core.generate_core.
    # Le harnais (scripts/harness.py) appelle la même fonction : une seule définition.
    from .dev_core import generate_core
    _core = generate_core(spec, project_workdir, project_name)

    if _core.template_failure:
        reason = _core.template_failure
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

    template_written: dict = _core.template_written
    stack_id = _core.stack_id
    stack_cfg = _core.stack_cfg
    spec_obj = _core.spec_obj
    _model_contexts: dict = _core.model_contexts
    _enriched_spec = _core.enriched_spec
    _page_nav_contracts: dict = _core.page_nav_contracts
    _design_system = _core.design_system
    _dev_tools_module.set_forbidden_imports(stack_cfg.get("forbidden_imports", []))

    if _core.prebuild_errors:
        logger.error(
            "[dev_graph] %d erreur(s) de cohérence pré-build — run annulé",
            len(_core.prebuild_errors),
        )
        _dev_tools_module.set_protected_files(None)
        _dev_tools_module.set_workdir(None)
        return {  # type: ignore[return-value]
            "messages": [], "spec": spec, "project_name": project_name, "run_id": run_id,
            "build_attempts": 0, "last_build_error": "\n".join(_core.prebuild_errors),
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

    # ── Pre-run commands (lues depuis stack config : npm deps, prisma generate) ──
    # Même fonction que le harnais (dev_core.run_pre_run_commands).
    from .dev_core import run_pre_run_commands
    _prev_cmd_ok, _pre_run_error = run_pre_run_commands(stack_cfg, project_workdir)
    if _pre_run_error:
        _dev_tools_module.set_protected_files(None)
        _dev_tools_module.set_workdir(None)
        return {  # type: ignore[return-value]
            "messages": [], "spec": spec, "project_name": project_name, "run_id": run_id,
            "build_attempts": 0, "last_build_error": _pre_run_error,
            "success": False, "build_command_executed": False,
            "build_exit_code": -1, "validated_files": [], "generation_turns": 0, "file_plan": None,
        }

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
    # (la recherche web a été retirée le 30 sept 2026 : bruit pour écrire une page)
    tools = list(DEV_TOOLS)

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
                            project_workdir, _service_map_str,
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

                # Dépendances disque exactes pour ce rôle (dev_context.py).
                _dep = build_role_context(_role, _path, spec_obj, project_workdir, _service_map_str, manifest=_level_a_manifest)

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
