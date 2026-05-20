
# agents/dev_prompts.py
"""
System prompt du dev agent v4 — Option A + Server Actions (30 Avril 2026).

Option A : lib/types.ts, lib/schemas.ts et lib/services/*.ts sont générés de
manière déterministe AVANT que le LLM démarre.  Le LLM ne génère QUE :
  - app/**/actions.ts   (Server Actions — mutations via service)
  - app/**/page.tsx     (Server Components — lecture directe Prisma)
  - app/api/webhooks/**/route.ts  (webhooks Clerk/Stripe seulement)

Level 1 scope : 2-4 modèles, CRUD, userId ownership — pas de RBAC ni logique complexe.
"""
from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from agents.project_spec import ProjectSpec


def _expected_files_from_spec(spec: "ProjectSpec") -> list[str]:
    """
    Checklist déterministe des fichiers que le LLM doit générer.
    Option A : lib/types.ts, lib/schemas.ts et lib/services/*.ts sont exclus
    car déjà pré-générés de manière déterministe.
    """
    files = []

    # Blueprint required_files (infrastructure)
    try:
        from agents.stack_config import load_stack_config
        stack_id = getattr(spec, "stack_id", "") or "nextjs-clerk-prisma"
        stack_cfg = load_stack_config(stack_id)
        required = stack_cfg.get("blueprint", {}).get("required_files", []) or []
        for path in required:
            if isinstance(path, str) and path.strip():
                files.append(path.strip().replace("\\", "/"))
    except Exception:
        pass

    # Server Actions — chemin dérivé via spec.get_list_page_for_model() (source de vérité unique)
    # Garantit que les paths ici == paths dans template_written → exclusion correcte du plan LLM.
    _action_paths: set[str] = set()
    for model in spec.models:
        list_page = spec.get_list_page_for_model(model.name)
        if list_page:
            route_dir = list_page.lstrip("/")
            _action_paths.add(f"app/{route_dir}/actions.ts")
    files.extend(sorted(_action_paths))

    # Webhooks routes (si présentes dans la spec)
    for route in spec.routes:
        path = route.path or ""
        if "webhook" in path.lower() or "stripe" in path.lower():
            rpath = path
            if rpath.startswith("/api"):
                rpath = rpath[4:]
            files.append(f"app/api{rpath.rstrip('/')}/route.ts")

    # Pages
    for page in spec.pages:
        ppath = page.path.strip("/")
        files.append("app/page.tsx" if not ppath else f"app/{ppath}/page.tsx")

    # page-client.tsx pour les pages custom [INTERACTIVE] uniquement (Level B — LLM).
    # Les page-client.tsx CRUD standard (list/create/detail/edit) sont Level A :
    # générés par dev_form_generator → dans template_written → filtrés par pre_written.
    # Le LLM ne les génère jamais. Ne pas les lister ici évite une checklist trompeuse.
    _crud_models_with_list: set[str] = set()
    for page in spec.pages:
        ptype = getattr(page, "page_type", None)
        model_name = getattr(page, "model", None)
        if ptype == "list" and model_name and getattr(page, "auth_required", True):
            _crud_models_with_list.add(model_name)

    pages_detail = getattr(spec, "pages_detail", {}) or {}
    if isinstance(pages_detail, dict):
        for path, detail in pages_detail.items():
            if "[INTERACTIVE]" in str(detail):
                # Vérifier que ce n'est pas une page model standard (déjà Level A)
                page_slug = path.strip("/")
                page_obj = next((p for p in spec.pages if p.path.strip("/") == page_slug), None)
                if page_obj and getattr(page_obj, "model", None) and getattr(page_obj, "page_type", None) in ("list", "create", "detail", "detail-slug"):
                    continue  # Level A — dev_form_generator gère ce fichier
                client_file = (
                    f"app/{page_slug}/page-client.tsx"
                    if page_slug else "app/page-client.tsx"
                )
                files.append(client_file)

    # Pages edit — PRÉ-GÉNÉRÉES (Level A) pour les modèles avec intent CRUD.
    _create_model_names: set[str] = {
        getattr(p, "model", None)
        for p in spec.pages
        if getattr(p, "page_type", None) == "create" and getattr(p, "model", None)
    }
    _edit_models = _crud_models_with_list & _create_model_names
    for model in spec.models:
        if model.name not in _edit_models:
            continue
        list_page = spec.get_list_page_for_model(model.name)
        if list_page:
            route_dir = list_page.lstrip("/")
            files.append(f"app/{route_dir}/[id]/edit/page.tsx")

    # Déduplique en préservant l'ordre
    seen: set[str] = set()
    result: list[str] = []
    for f in files:
        norm = str(f).strip().replace("\\", "/")
        if not norm or norm in seen:
            continue
        seen.add(norm)
        result.append(norm)
    return result


def _build_mandatory_rag_block(spec: "ProjectSpec") -> str:
    """
    Requêtes Qdrant déclenchées en Python AVANT la génération, basées sur le contenu
    du brief. Standards sélectionnés automatiquement → injectés dans le prompt.
    """
    try:
        from agents.shared_tools import rag_search as _rag_fn
        from agents.stack_config import load_stack_config
    except Exception:
        return ""

    contexts: list[str] = ["always"]

    has_relations = any(
        any(f.name != "id" and f.name.endswith("Id") for f in m.fields)
        for m in spec.models
    )
    if has_relations:
        contexts.append("relation-models")

    if len(spec.models) >= 2:
        contexts.append("multi-table")

    if spec.pages:
        contexts.append("interactive-pages")

    has_dynamic_pages = any("[" in p.path for p in spec.pages)
    if has_dynamic_pages:
        contexts.append("dynamic-pages")

    # UI quality — déclenché si la spec a des pages custom [INTERACTIVE] (Level B).
    # Les page-client.tsx CRUD standard sont Level A — ZONE_UI_PAGE_CLIENT inactive.
    # Ce contexte cible uniquement les pages custom (dashboard, hub, profil) où le LLM
    # génère le composant Client depuis les pages_detail du brief.
    _pages_detail = getattr(spec, "pages_detail", {}) or {}
    has_custom_interactive = any(
        "[INTERACTIVE]" in str(v)
        for v in _pages_detail.values()
    )
    if has_custom_interactive:
        contexts.append("page_client_ui")

    # Requêtes alignées sur le format RULE: des standards Qdrant (post-Option-A).
    # Termes en français technique pour maximiser le recall avec les standards reformatés.
    CONTEXT_QUERIES: dict[str, str] = {
        "always": (
            "auth userId guard obligatoire Prisma ownership Server Action "
            "sécurité validation Zod revalidatePath throw Unauthorized"
        ),
        "relation-models": (
            "N+1 prevention include select nested relation Prisma findUnique "
            "boucle Promise.all jointure optimisée"
        ),
        "multi-table": (
            "prisma transaction séquentiel rollback multi-table create "
            "atomic update plusieurs modèles"
        ),
        "interactive-pages": (
            "'use client' directive useState onClick formulaire handler "
            "Client Component interactif Server Component split revalidatePath"
        ),
        "dynamic-pages": (
            "notFound import next/navigation page dynamique [id] params "
            "Server Component getById service null absent redirect 404"
        ),
        "page_client_ui": (
            "custom page-client.tsx dashboard hub profile 'use client' "
            "Client Component SerializedXxx props useState typed revalidatePath"
        ),
    }

    snippets: list[str] = []
    seen_texts: set[str] = set()

    stack_id = getattr(spec, "stack_id", "nextjs-clerk-prisma")

    for ctx in contexts:
        query = CONTEXT_QUERIES.get(ctx, "")
        if not query:
            continue
        try:
            logger.info("[mandatory-rag] ctx=%-18s | q=%r", ctx, query[:70])
            result = _rag_fn.invoke({"query": query})
            if result and not result.startswith("[RAG]") and result not in seen_texts:
                seen_texts.add(result)
                snippets.append(f"[contexte: {ctx}]\n{result[:600]}")
                _n_stds = len([s for s in result.split("---") if s.strip()])
                logger.info("[mandatory-rag] ctx=%-18s | %d standard(s) injectés", ctx, _n_stds)
            elif result and result.startswith("[RAG]"):
                logger.warning("[mandatory-rag] ctx=%-18s | RAG indisponible ou vide", ctx)
        except Exception:
            pass

    if not snippets:
        return ""

    joined = "\n\n---\n\n".join(snippets)
    return f"""
══════════════════════════════════════════════════════════════
STANDARDS TECHNIQUES APPLICABLES À CE BRIEF (Qdrant)
══════════════════════════════════════════════════════════════
Ces standards ont été sélectionnés automatiquement selon le contenu du brief.
Applique-les lors de la génération — ne les ignore pas.

{joined}
"""


def get_page_detail_hint(spec: "ProjectSpec", page_path: str) -> str:
    """
    Retourne le bloc pages_detail pour une page spécifique.
    Injecté par executor_node au moment de générer cette page (Phase-Aware).
    Retourne "" si aucun détail n'est défini pour ce chemin.
    """
    pages_detail = getattr(spec, "pages_detail", {}) or {}
    if not isinstance(pages_detail, dict):
        return ""
    detail = pages_detail.get(page_path) or pages_detail.get("/" + page_path.strip("/"))
    if not detail:
        return ""
    detail_str = str(detail).strip()
    if "[INTERACTIVE]" in detail_str:
        page_slug = page_path.strip("/").replace("/", "-") or "home"
        comp_name = page_slug.title().replace("-", "")
        client_file = (
            f"app/{page_path.strip('/')}/page-client.tsx"
            if page_path.strip("/") else "app/page-client.tsx"
        )
        detail_str += (
            f"\n⚠️  SPLIT OBLIGATOIRE : créer {client_file} avec '\"use client\"' en ligne 1. "
            f"page.tsx reste Server Component (fetch données) et rend <{comp_name}Client ... />. "
            f"Import DEFAULT : import {comp_name}Client from './page-client' (jamais named). "
            f"Export DEFAULT dans {client_file} : export default function {comp_name}Client(...)."
        )
    return (
        f"CONTENU ATTENDU POUR {page_path} :\n"
        f"{detail_str}"
    )


def build_system_prompt(
    spec: "ProjectSpec",
    pre_written_files: list[str] | None = None,
    service_map: str = "",
    prisma_type_map: dict | None = None,
) -> str:
    """
    Construit le system prompt pour le dev agent v4 — Option A (Phase-Aware).
    Rendu via Jinja2 depuis dev_system_prompt.j2 (StrictUndefined — toute variable
    manquante lève UndefinedError immédiatement, sans fallback silencieux).

    Phase-Aware : pages_detail et action_map sont EXCLUS du system prompt (trop lourds).
    Ils sont injectés par executor_node via HumanMessage au moment de générer chaque page.
    """
    import os
    from jinja2 import Environment, StrictUndefined
    pre_written: set[str] = set(pre_written_files or [])
    expected_files = _expected_files_from_spec(spec)
    files_to_generate = [f for f in expected_files if f not in pre_written]
    files_checklist = "\n".join(f"  - {f}" for f in files_to_generate)

    # Règles stack depuis rules_dev.md
    stack_rules_block = ""
    try:
        from utils.prompt_loader import load_stack_rules_only
        stack_id = getattr(spec, "stack_id", "") or "nextjs-clerk-prisma"
        stack_rules = load_stack_rules_only("dev", stack_id)
        if stack_rules.strip():
            stack_rules_block = f"""
══════════════════════════════════════════════════════════════
RÈGLES TECHNIQUES STACK (source : rules_dev.md — priorité absolue)
══════════════════════════════════════════════════════════════
{stack_rules}
"""
    except Exception:
        pass

    prisma_block = spec.to_prisma_schema_block()

    pages_summary = "\n".join(
        f"  - {p.path}{' (publique)' if not p.auth_required else ''}"
        for p in spec.pages
    )

    # Routes (webhooks seulement — les mutations sont maintenant des Server Actions)
    webhook_routes = [r for r in spec.routes if "webhook" in r.path.lower() or "stripe" in r.path.lower()]
    routes_summary = "\n".join(
        f"  - {r.method} {r.path}  [webhook]"
        for r in webhook_routes
    ) or "  (aucune route API — mutations gérées par les Server Actions)"

    # pages_detail retiré du system prompt (Phase-Aware).
    # Injecté par executor_node via get_page_detail_hint() au moment de générer chaque page.
    # Gain : ~2000 tokens économisés sur le system prompt.

    # Service Map — bloc compact des services pré-générés
    service_map_block = ""
    if service_map:
        service_map_block = f"""
══════════════════════════════════════════════════════════════
SERVICES DAL PRÉ-GÉNÉRÉS — UTILISE-LES, NE LES RECRÉE PAS
══════════════════════════════════════════════════════════════
{service_map}
⚠️  Ces fichiers sont déjà écrits et protégés.
JAMAIS prisma directement dans actions.ts ou page.tsx — toujours via le service.
JAMAIS de fonctions nommées : ✅ projectService.create()  ❌ createProject()
"""
    else:
        # Fallback si service_map non disponible
        service_map_block = """
══════════════════════════════════════════════════════════════
SERVICES DAL (pré-générés dans lib/services/)
══════════════════════════════════════════════════════════════
Les services sont dans lib/services/<model>.service.ts — NE PAS LES RÉÉCRIRE.
Convention : import { projectService } from '@/lib/services/project.service'
Méthodes :
  .getAll(userId)              → Promise<SerializedXxx[]>
  .getById(userId, id)         → Promise<SerializedXxx>  (notFound() si absent — jamais null)
  .create(userId, data)        → Promise<Xxx>
  .update(id, data)            → Promise<Xxx>
  .delete(userId, id)          → Promise<void>
⚠️ getById ne retourne JAMAIS null — pas besoin de null-check ni de notFound() dans la page.
"""

    # DMMF Prisma — types réels des champs (extrait après prisma generate)
    dmmf_block = ""
    if prisma_type_map:
        try:
            from .dev_prisma_extractor import format_type_map_for_prompt
            dmmf_block = format_type_map_for_prompt(prisma_type_map)
        except Exception:
            pass

    # Spec JSON compacte — routes CRUD exclues (ce sont des Server Actions, pas des route.ts)
    _webhook_routes_only = [
        f"{r.method} {r.path}" for r in spec.routes
        if "webhook" in r.path.lower() or "stripe" in r.path.lower()
    ]
    spec_json = json.dumps({
        "models": [m.name for m in spec.models],
        "pages": [p.path for p in spec.pages],
        **({"webhooks": _webhook_routes_only} if _webhook_routes_only else {}),
        "fingerprint": spec.spec_fingerprint,
    }, ensure_ascii=False)

    mandatory_rag_block = _build_mandatory_rag_block(spec)

    # Fichiers pré-générés (à ne pas réécrire)
    pre_written_block = ""
    if pre_written:
        pre_written_list = "\n".join(f"  - {f}" for f in sorted(pre_written))
        pre_written_block = (
            "\n══════════════════════════════════════════════════════════════\n"
            "FICHIERS PRÉ-GÉNÉRÉS — NE PAS RÉÉCRIRE\n"
            "══════════════════════════════════════════════════════════════\n"
            f"Ces fichiers sont CORRECTS et COMPLETS — ne les réécrits JAMAIS :\n{pre_written_list}\n"
        )

    _tpl_path = os.path.join(os.path.dirname(__file__), "dev_system_prompt.j2")
    with open(_tpl_path, encoding="utf-8") as _f:
        _tpl_source = _f.read()

    env = Environment(undefined=StrictUndefined)
    rendered = env.from_string(_tpl_source).render(
        mandatory_rag_block=mandatory_rag_block,
        service_map_block=service_map_block,
        dmmf_block=dmmf_block,
        pre_written_block=pre_written_block,
        spec_json=spec_json,
        pages_summary=pages_summary,
        routes_summary=routes_summary,
        prisma_block=prisma_block,
        files_checklist=files_checklist,
        stack_rules_block=stack_rules_block,
    )
    return rendered.replace("{WORKDIR}", "/app/generated-projects")
