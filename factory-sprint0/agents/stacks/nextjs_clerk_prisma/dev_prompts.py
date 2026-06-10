
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

    # Fallback Level A → LLM : inclure page-client.tsx CRUD dans la checklist LLM.
    # Si Level A a réussi → fichier dans template_written → dans pre_written_files
    # → filtré par build_system_prompt (files_to_generate) → LLM ne le régénère pas.
    # Si Level A a échoué silencieusement → pas dans pre_written_files → LLM le génère
    # → évite TS2307 "Cannot find module './page-client'" sur page.tsx généré.
    for _pc_page in spec.pages:
        _pc_ptype = getattr(_pc_page, "page_type", None)
        if _pc_ptype not in ("list", "create", "detail", "detail-slug"):
            continue
        _pc_path = _pc_page.path.strip("/")
        _pc_file = f"app/{_pc_path}/page-client.tsx" if _pc_path else "app/page-client.tsx"
        files.append(_pc_file)

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
            _model_has_slug = any(f.name.lower() == "slug" for f in model.fields)
            _slug_or_id = "[slug]" if _model_has_slug else "[id]"
            files.append(f"app/{route_dir}/{_slug_or_id}/edit/page.tsx")

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

    # Territoire LLM : layout.tsx, page.tsx custom (auth + appel service), page-client.tsx [INTERACTIVE].
    # Les services, actions, types, schemas, pages CRUD sont Level A (pré-générés) → pas de standards Level A ici.

    if spec.pages:
        contexts.append("interactive-pages")

    has_dynamic_pages = any("[" in p.path for p in spec.pages)
    if has_dynamic_pages:
        contexts.append("dynamic-pages")

    # Pages publiques — déclenché si au moins une page sans auth (blog, recettes, articles).
    has_public_pages = any(not p.auth_required for p in spec.pages)
    if has_public_pages:
        contexts.append("public-pages")

    # UI Level B — déclenché si la spec a des pages custom [INTERACTIVE].
    # Les page-client.tsx CRUD standard sont Level A — cette query cible uniquement
    # les pages custom (dashboard, hub, landing) générées par le LLM depuis pages_detail.
    _pages_detail = getattr(spec, "pages_detail", {}) or {}
    has_custom_interactive = any(
        (isinstance(v, dict) and v.get("interactive", False))
        or (isinstance(v, str) and "[INTERACTIVE]" in v)
        for v in _pages_detail.values()
    )
    if has_custom_interactive:
        contexts.append("page_client_ui")

    # Requêtes ciblées sur le territoire réel du LLM (post-Level-A).
    # NE PAS inclure : N+1 (services), transactions Prisma (services), Zod (actions) — Level A.
    CONTEXT_QUERIES: dict[str, str] = {
        "always": (
            "auth() userId guard page.tsx Server Component redirect sign-in "
            "Clerk protection route authentifiée await auth"
        ),
        "interactive-pages": (
            "useActionState formulaire form Server Action 'use client' "
            "page-client isPending error formAction submit"
        ),
        "dynamic-pages": (
            "notFound [id] params page dynamique Server Component "
            "getById service null absent redirect 404 next/navigation "
            "import Link from next/link Link href navigation cliquable lien"
        ),
        "public-pages": (
            "page publique sans auth no auth_required getPublished "
            "visiteur liste publique without userId public route"
        ),
        "page_client_ui": (
            "dashboard SerializedXxx props Client Component "
            "empty state liste vide Link navigation href next/link "
            "Button asChild ButtonProps import next/link next/image"
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


def _page_detail_interactive_suffix(page_path: str) -> str:
    """Bloc SPLIT obligatoire injecté quand interactive=True."""
    page_slug = page_path.strip("/").replace("/", "-") or "home"
    comp_name = page_slug.title().replace("-", "")
    client_file = (
        f"app/{page_path.strip('/')}/page-client.tsx"
        if page_path.strip("/") else "app/page-client.tsx"
    )
    return (
        f"\n⚠️  SPLIT OBLIGATOIRE : créer {client_file} avec '\"use client\"' en ligne 1. "
        f"page.tsx reste Server Component (fetch données) et rend <{comp_name}Client ... />. "
        f"Import DEFAULT : import {comp_name}Client from './page-client'. "
        f"Export DEFAULT dans {client_file} : export default function {comp_name}Client(...)."
    )


def get_page_detail_hint(spec: "ProjectSpec", page_path: str) -> str:
    """
    Retourne le bloc pages_detail pour une page spécifique.
    Injecté par executor_node au moment de générer cette page (Phase-Aware).

    Gère deux formats :
      - dict structuré (D1 — nouveau) : {description, data_fetches, interactive}
      - str (backward compat — ancien format avec [INTERACTIVE])
    """
    pages_detail = getattr(spec, "pages_detail", {}) or {}
    if not isinstance(pages_detail, dict):
        return ""
    detail = pages_detail.get(page_path) or pages_detail.get("/" + page_path.strip("/"))
    if not detail:
        return ""

    # ── Format structuré (D1) ──────────────────────────────────────────────────
    if isinstance(detail, dict):
        desc = str(detail.get("description", "")).strip()
        fetches = detail.get("data_fetches", []) or []
        interactive = bool(detail.get("interactive", False))

        lines = [f"CONTENU ATTENDU POUR {page_path} :"]
        if desc:
            lines.append(desc)
        if fetches:
            lines.append("DONNÉES À CHARGER (Server Component, dans l'ordre) :")
            for f in fetches:
                svc = str(f.get("service", "")).strip()
                as_var = str(f.get("as", f.get("as_var", ""))).strip()
                if svc:
                    lines.append(f"  const {as_var} = await {svc}" if as_var else f"  await {svc}")
        if interactive:
            lines.append(_page_detail_interactive_suffix(page_path))
        return "\n".join(lines)

    # ── Format texte libre (backward compat) ──────────────────────────────────
    detail_str = str(detail).strip()
    if "[INTERACTIVE]" in detail_str:
        detail_str += _page_detail_interactive_suffix(page_path)
    return f"CONTENU ATTENDU POUR {page_path} :\n{detail_str}"


def build_system_prompt(
    spec: "ProjectSpec",
    pre_written_files: list[str] | None = None,
    service_map: str = "",
    prisma_type_map: dict | None = None,
    design_system: dict | None = None,
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

    # Design system — bloc injecté dans le system prompt pour guider le LLM
    # Les couleurs sont des CSS variables dans globals.css. Le LLM utilise des classes sémantiques.
    design_block = ""
    if design_system:
        primary = design_system.get("primary_color", "blue-600")
        brand = design_system.get("brand_name", "")
        mood = design_system.get("mood", "")
        density = design_system.get("density", "")
        sidebar_bg = design_system.get("sidebar_bg", "")
        animation = design_system.get("animation_level", "")
        design_block = (
            "\n══════════════════════════════════════════════════════════════\n"
            "DESIGN SYSTEM — TOKENS SÉMANTIQUES (CSS variables, shadcn/ui)\n"
            "══════════════════════════════════════════════════════════════\n"
            f"primary_color configuré : {primary} → accessible via la classe Tailwind `primary`\n"
            "\nTOKENS TAILWIND — utilise ces classes dans tes pages custom :\n"
            "  boutons primaires : bg-primary hover:bg-primary/85 text-white font-medium\n"
            "  liens / accents   : text-primary hover:text-primary/80\n"
            "  bordures colorées : border-primary\n"
            "  focus rings       : focus:ring-primary focus:ring-2 focus:ring-offset-2\n"
            "  fond léger hover  : hover:bg-primary/10\n"
            "  texte principal   : text-foreground\n"
            "  texte secondaire  : text-muted-foreground\n"
            "  fond carte        : bg-card border-border\n"
            "  fond page         : bg-background\n"
            + (f"\nbrand_name : {brand}" if brand else "")
            + (f"\nmood : {mood}" if mood else "")
            + (f"\ndensity : {density}  (compact → espacement réduit ; spacious → espacement généreux)" if density else "")
            + (f"\nsidebar_bg : {sidebar_bg}" if sidebar_bg else "")
            + (f"\nanimation_level : {animation}  (none → pas d'animations ; standard → transition-colors ; enhanced → keyframes)" if animation else "")
            + "\n\nCOMPOSANTS UI DISPONIBLES (shadcn/ui — dans components/ui/) :\n"
            "  import { Button }   from '@/components/ui/button'\n"
            "  import { Input }    from '@/components/ui/input'\n"
            "  import { Textarea } from '@/components/ui/textarea'\n"
            "  import { Label }    from '@/components/ui/label'\n"
            "  import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'\n"
            "  import { Badge }    from '@/components/ui/badge'\n"
            "  import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from '@/components/ui/table'\n"
            "  import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'\n"
            "  import { Empty }    from '@/components/Empty'     ← état vide custom\n"
            "  import { StatCard } from '@/components/StatCard'  ← carte métrique custom\n"
            "\n⚠️  N'utilise JAMAIS bg-blue-600 / text-blue-600 ni aucune couleur Tailwind hardcodée.\n"
            "     Utilise TOUJOURS les tokens sémantiques ci-dessus (bg-primary, text-foreground, etc.).\n"
        )

    # page_links — contrat de navigation par page
    page_links_block = ""
    _page_links: dict = getattr(spec, "page_links", None) or {}
    if _page_links:
        _lines = []
        for path, links in _page_links.items():
            _lines.append(f"  {path} → {', '.join(links) if links else '(aucun lien)'}")
        page_links_block = (
            "\n══════════════════════════════════════════════════════════════\n"
            "CONTRAT DE NAVIGATION — LIENS AUTORISÉS PAR PAGE\n"
            "══════════════════════════════════════════════════════════════\n"
            "Tu ne peux générer des <Link href='...'> QUE vers les chemins listés ci-dessous.\n"
            "Tout autre chemin est INTERDIT — même s'il semble naturel (ex: /[id]/edit non déclaré).\n"
            + "\n".join(_lines) + "\n"
        )

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
        page_links_block=page_links_block,
        design_block=design_block,
    )
    return rendered.replace("{WORKDIR}", "/app/generated-projects")
