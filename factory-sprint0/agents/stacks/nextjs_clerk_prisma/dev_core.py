# agents/stacks/nextjs_clerk_prisma/dev_core.py
"""
Génération déterministe du cœur d'une app — la séquence complète des générateurs.

Une seule définition de la séquence (USINE.md §4.6, règle 1) : appelée par
`dev_graph.run_dev_agent` en production ET par le harnais (`scripts/harness.py`).
`generate_core` : aucun appel LLM, aucune commande npm — entrée = la déclaration (le dict
ProjectSpec reçu de l'architect), sortie = les fichiers écrits dans `project_workdir`.
`run_pre_run_commands` : les commandes de préparation (dépendances npm, prisma generate).

Code déplacé tel quel depuis dev_graph.py (30 sept 2026) — comportement inchangé.
Hors de ce module (dépendent d'un LLM ou de node_modules) : design brief, enrichissement
du shell, régénération décorée des page-clients, executor.
"""
from __future__ import annotations

import logging
import os
import re
import subprocess
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class CoreGeneration:
    """Résultat de generate_core. `template_failure` non vide = génération abandonnée dès
    les templates ; `prebuild_errors` non vide = générateur cœur planté ou incohérence
    page.tsx → page-client.tsx (le run doit s'arrêter avant tout LLM)."""
    template_written: dict = field(default_factory=dict)
    template_failure: str = ""
    prebuild_errors: list = field(default_factory=list)
    stack_id: str = ""
    stack_cfg: dict = field(default_factory=dict)
    spec_obj: object = None
    model_contexts: dict = field(default_factory=dict)
    enriched_spec: object = None
    page_nav_contracts: dict = field(default_factory=dict)
    design_system: dict = field(default_factory=dict)


def generate_core(spec: dict, project_workdir: str, project_name: str) -> CoreGeneration:
    """Écrit tous les fichiers déterministes de l'app dans project_workdir (qui doit exister).

    Lève une exception si schema.prisma ou les contextes modèles ne peuvent pas être
    construits (même comportement FATAL qu'avant l'extraction).
    """
    result = CoreGeneration()

    # ── Pré-génération des fichiers templates ────────────────────────
    # package.json, middleware.ts, app/layout.tsx, tsconfig.json, etc.
    # BLOQUANT : sans package.json, npm install échoue et le run entier est compromis.
    template_written: dict = {}
    _template_error: str = ""
    # Crashs des générateurs déterministes cœur. Un générateur qui plante ne doit PAS
    # basculer en douce vers le LLM (Level A dégradé en improvisation, en silence) : on
    # collecte ici et on abandonne le run avant la génération LLM (voir prebuild_errors).
    _generator_errors: list[str] = []
    stack_cfg: dict = {}
    try:
        from .dev_file_ops import write_template_files
        from agents.stack_config import load_stack_config
        stack_id = spec.get("stack_id", "") or ""
        if not stack_id:
            stack_id = "nextjs-clerk-prisma"
            logger.warning("[dev_core] stack_id absent de la spec — fallback sur '%s'", stack_id)
        result.stack_id = stack_id
        stack_cfg = load_stack_config(stack_id)
        result.stack_cfg = stack_cfg
        template_written = write_template_files(project_workdir, stack_cfg, project_name, stack_id, spec=spec)
        logger.info(
            f"[dev_core] {len(template_written)} fichiers pré-générés depuis templates : "
            f"{list(template_written.keys())}"
        )
    except Exception as _te:
        _template_error = f"write_template_files échoué : {_te}"
        logger.error(f"[dev_core] {_template_error}")

    result.template_written = template_written
    if _template_error or "package.json" not in template_written:
        result.template_failure = _template_error or "package.json absent des templates"
        logger.error(f"[dev_core] ABORT — {result.template_failure}")
        return result

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
            f"[dev_core] schema.prisma matérialisé depuis ProjectSpec "
            f"({len(spec_obj.models)} modèles)"
        )
    except Exception as _se:
        logger.error(f"[dev_core] schema.prisma FATAL : {_se}", exc_info=True)
        raise
    result.spec_obj = spec_obj

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
                "[dev_core] %d ModelGenerationContext calculés (enriched_spec=%s)",
                len(_model_contexts), bool(_enriched_spec),
            )
        except Exception as _mc_err:
            logger.error(f"[dev_core] build_all_contexts FATAL : {_mc_err}", exc_info=True)
            raise RuntimeError(f"build_all_contexts failed: {_mc_err}") from _mc_err
    result.model_contexts = _model_contexts
    result.enriched_spec = _enriched_spec

    # ── Niveau 1 — Page Contract Calculator ─────────────────────────────────
    # Contrats navigation/données pour toutes les pages modèle.
    # Injectés dans _file_brief par executor_node (dev_graph).
    # Distinct de _page_contracts (planner.py) qui couvre uniquement les pages
    # [INTERACTIVE] et injecte des hints service dans context_hint du plan.
    if spec_obj is not None and _model_contexts:
        try:
            from .dev_page_contract import compute_page_contracts as _compute_contracts
            result.page_nav_contracts = _compute_contracts(spec_obj, _model_contexts)
        except Exception as _pc_err:
            logger.warning("[dev_core] page_contract non bloquant : %s", _pc_err)

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
            logger.info("[dev_core] lib/types.ts généré de manière déterministe")
        except Exception as _tg_err:
            _template_error = f"TYPES_GENERATOR_FAILED: {_tg_err}"
            logger.error(f"[dev_core] {_template_error}")

    # ── Génération déterministe : lib/schemas.ts ─────────────────────
    # BLOQUANT : les Server Actions importent les schemas Zod pour valider les inputs.
    if spec_obj is not None and not _template_error:
        try:
            from .dev_zod_generator import generate_schemas_file
            _schemas_result = generate_schemas_file(spec_obj, project_workdir, contexts=_model_contexts or None)
            if _schemas_result:
                template_written[_schemas_result.path] = _schemas_result.content
                logger.info("[dev_core] lib/schemas.ts généré de manière déterministe")
        except Exception as _zg_err:
            _template_error = f"ZOD_GENERATOR_FAILED: {_zg_err}"
            logger.error(f"[dev_core] {_template_error}")

    # ── Génération déterministe : lib/services/*.ts ───────────────────
    if spec_obj is not None:
        try:
            from .dev_service_generator import generate_service_files
            _svc_written = generate_service_files(spec_obj, project_workdir, contexts=_model_contexts or None, enriched_spec=_enriched_spec)
            template_written.update(_svc_written)
            logger.info("[dev_core] %d services DAL générés de manière déterministe", len(_svc_written))
        except Exception as _svc_err:
            _generator_errors.append(f"SERVICE_GENERATOR_FAILED: {_svc_err}")
            logger.error("[dev_core] service generator a échoué (bloquant) : %s", _svc_err)

    # ── Génération déterministe : prisma/seed.ts (Preview local, dev-only) ──
    # Données de démonstration. Exclu du build (tsconfig) → un bug de seed ne casse
    # jamais l'app. Non bloquant : une erreur ici n'empêche pas la génération.
    if spec_obj is not None and _model_contexts:
        try:
            from .dev_seed_generator import generate_seed_file
            _seed_written = generate_seed_file(spec_obj, project_workdir, contexts=_model_contexts)
            template_written.update(_seed_written)
            logger.info("[dev_core] prisma/seed.ts généré (%d modèle(s))", len(_model_contexts))
        except Exception as _seed_err:
            logger.warning("[dev_core] seed generator échoué (non bloquant) : %s", _seed_err)

    # ── Génération déterministe : app/**/actions.ts ───────────────────
    if spec_obj is not None:
        try:
            from .dev_actions_generator import generate_action_files
            _act_written = generate_action_files(spec_obj, project_workdir, model_contexts=_model_contexts or None)
            template_written.update(_act_written)
            logger.info("[dev_core] %d fichiers actions.ts générés de manière déterministe", len(_act_written))
        except Exception as _act_err:
            _generator_errors.append(f"ACTIONS_GENERATOR_FAILED: {_act_err}")
            logger.error("[dev_core] actions generator a échoué (bloquant) : %s", _act_err)

    # ── ORACLE (le 5ᵉ lot) : chaque case émet sa preuve, dérivée de la déclaration ──
    # Route dev-only /api/_oracle, lancée contre l'app qui tourne (ancrage AVAL, hors du miroir).
    if spec_obj is not None:
        try:
            from .dev_oracle_generator import generate_oracle_file
            _oracle_written = generate_oracle_file(spec_obj, project_workdir, contexts=_model_contexts)
            template_written.update(_oracle_written)
            if _oracle_written:
                logger.info("[dev_core] oracle généré : %s", list(_oracle_written.keys()))
        except Exception as _or_err:
            # Non bloquant : un oracle absent ne casse jamais un build.
            logger.warning("[dev_core] oracle generator non bloquant : %s", _or_err)

    # ══ UI INFRASTRUCTURE — design system, layout, navigation ════════════════════
    # Générés avant les pages pour que les composants UI existent sur disque
    # quand le LLM démarre. Tous lockés dans template_written.
    _design_system = spec.get("design_system") or getattr(spec_obj, "design_system", {}) or {}
    result.design_system = _design_system

    # ── Design system : composants UI + tailwind.config.js + globals.css ─────
    if spec_obj is not None:
        try:
            from .dev_design_system_generator import generate_design_system
            _ds_files = generate_design_system(project_workdir, design_system=_design_system)
            template_written.update(_ds_files)
            logger.info("[dev_core] design system généré (%d fichiers, primary=%s)",
                        len(_ds_files), _design_system.get("primary_color", "blue-600"))
        except Exception as _ds_err:
            logger.warning("[dev_core] design_system_generator non bloquant : %s", _ds_err)

    # ── Layout + DashboardShell — avec les vraies couleurs du brief ───────────
    if spec_obj is not None:
        try:
            from .dev_layout_generator import generate_layout
            _layout_files = generate_layout(project_workdir, project_name, spec, spec_obj=spec_obj, enriched_spec=_enriched_spec)
            template_written.update(_layout_files)
            logger.info("[dev_core] layout shell généré (layout_type=%s, sidebar_bg=%s)",
                        _design_system.get("layout_type", "sidebar"),
                        _design_system.get("sidebar_bg", "white"))
        except Exception as _ly_err:
            logger.warning("[dev_core] layout_generator non bloquant : %s", _ly_err)

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
            logger.error("[dev_core] page generators ont échoué (bloquant) : %s", _pg_err)

    # ── Génération déterministe : SEO (sitemap.ts + robots.ts) ────────────────
    # Sprint 5 (Type D-complet) — uniquement si l'app a des pages publiques.
    # Le generateMetadata des pages detail-slug publiques est émis par _gen_page_full.
    if spec_obj is not None:
        try:
            from .dev_seo_generator import generate_seo_files
            _seo_files = generate_seo_files(spec_obj, _model_contexts or {}, project_workdir)
            template_written.update(_seo_files)
            if _seo_files:
                logger.info("[dev_core] %d fichiers SEO générés : %s", len(_seo_files), list(_seo_files.keys()))
        except Exception as _seo_err:
            logger.warning(f"[dev_core] seo generator non bloquant : {_seo_err}")

    # ── Génération déterministe : page-client.tsx (Level A) ──────────────────
    # Tous les page-client.tsx CRUD standard sont déterministes :
    # list (table Tailwind), create (form + FK selects), edit (form + defaultValues), detail.
    # Ces fichiers sont ajoutés à template_written → le LLM ne peut pas les écraser.
    # Les page-client.tsx custom (dashboard, hub, etc.) restent au LLM (Level B).
    if spec_obj is not None and _model_contexts:
        try:
            from .dev_form_generator import generate_all_page_clients
            _form_files = generate_all_page_clients(spec_obj, _model_contexts, project_workdir, enriched_spec=_enriched_spec, design_system=_design_system)
            template_written.update(_form_files)
            logger.info("[dev_core] %d page-client.tsx générés de manière déterministe", len(_form_files))
        except Exception as _fg_err:
            _generator_errors.append(f"FORM_GENERATOR_FAILED: {_fg_err}")
            logger.error("[dev_core] form generator a échoué (bloquant) : %s", _fg_err)

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
                logger.info("[dev_core] %d fichier(s) parent detail auto-générés", len(_parent_detail_files))
        except Exception as _pd_err:
            _generator_errors.append(f"PARENT_DETAIL_GENERATOR_FAILED: {_pd_err}")
            logger.error("[dev_core] parent detail pages ont échoué (bloquant) : %s", _pd_err)

    # Les pages détail parent+enfants sont gérées structurellement :
    # - page.tsx : déterministe via generate_page_stubs (flux normal, model présent)
    # - page-client.tsx : déterministe via module_detail_with_children
    #   (détection via ctx.relation_fields dans dev_form_generator — pas de marqueurs texte)

    # ── Hub page déterministe : app/dashboard/page.tsx ────────────────────────
    # Le LLM oubliait régulièrement `import Link from 'next/link'` sur cette page → build fail.
    # La hub page est entièrement dérivable du spec_obj → on la génère avant le LLM.
    if spec_obj is not None and _model_contexts:
        try:
            from .dev_hub_generator import generate_hub_page as _gen_hub
            _hub_files = _gen_hub(spec_obj, _model_contexts, project_workdir, pages_detail=getattr(spec_obj, "pages_detail", {}) or {})
            template_written.update(_hub_files)
        except Exception as _hub_err:
            _generator_errors.append(f"HUB_GENERATOR_FAILED: {_hub_err}")
            logger.error("[dev_core] hub_generator a échoué (bloquant) : %s", _hub_err)

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
            logger.error("[dev_core] public home generator a échoué (bloquant) : %s", _home_err)

    # ── Feature modules (registry déclaratif depuis stack JSON config) ───────
    if spec_obj is not None and _model_contexts:
        try:
            from .feature_module import load_feature_modules, run_feature_modules
            _fm_names = stack_cfg.get("feature_modules", [])
            load_feature_modules(_fm_names, package=__name__.rsplit(".", 1)[0])
            _feature_files = run_feature_modules(spec_obj, _model_contexts, _enriched_spec, project_workdir, design_system=_design_system)
            template_written.update(_feature_files)
            if _feature_files:
                logger.info("[dev_core] %d fichier(s) de feature modules", len(_feature_files))
        except Exception as _fm_err:
            _generator_errors.append(f"FEATURE_MODULES_FAILED: {_fm_err}")
            logger.error("[dev_core] feature_modules ont échoué (bloquant) : %s", _fm_err)

    # ── Guard pré-build : cohérence page.tsx → page-client.tsx ─────────────
    # Après tous les générateurs déterministes, vérifie que chaque page.tsx
    # qui importe './page-client' a son page-client.tsx dans template_written.
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
            logger.error("[dev_core] %s", _prebuild_errors[-1])

    result.prebuild_errors = _prebuild_errors
    return result


def run_pre_run_commands(stack_cfg: dict, project_workdir: str) -> tuple[bool, str]:
    """Exécute les "pre_run_commands" de la config stack (copie des dépendances npm,
    prisma generate…). Respecte blocking + requires_prev.

    Retourne (dernière_commande_ok, erreur_bloquante). erreur_bloquante non vide =
    une commande bloquante a échoué → l'appelant doit arrêter.
    Déplacé tel quel depuis dev_graph.py (30 sept 2026) ; partagé avec le harnais.
    """
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
            logger.warning("[dev_core] pre-run '%s' skipped — commande précédente échouée", _cmd)
            continue
        try:
            logger.info("[dev_core] pre-run : %s ...", _cmd)
            _pr = subprocess.run(
                _cmd, shell=_shell, capture_output=True, text=True,
                timeout=_tout, cwd=project_workdir, env=_pre_run_env,
            )
            if _pr.returncode == 0:
                _prev_cmd_ok = True
                logger.info("[dev_core] pre-run OK : %s", _cmd)
            else:
                _prev_cmd_ok = False
                _out = (_pr.stdout + _pr.stderr)[:400]
                logger.warning("[dev_core] pre-run FAILED '%s' (exit %d): %s", _cmd, _pr.returncode, _out)
                if _block:
                    return False, f"PRE_RUN_FAILED ({_cmd}): {_out[:300]}"
        except subprocess.TimeoutExpired:
            _prev_cmd_ok = False
            logger.warning("[dev_core] pre-run TIMEOUT '%s' (>%ds)", _cmd, _tout)
            if _block:
                return False, f"PRE_RUN_TIMEOUT ({_cmd})"
        except Exception as _cmd_err:
            _prev_cmd_ok = False
            logger.warning("[dev_core] pre-run exception '%s': %s", _cmd, _cmd_err)
    return _prev_cmd_ok, ""
