
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

    # Server Actions — chemin dérivé via _find_list_page (même logique que dev_actions_generator)
    # Garantit que les paths ici == paths dans template_written → exclusion correcte du plan LLM.
    try:
        from .dev_actions_generator import _find_list_page as _flp
        _action_paths: set[str] = set()
        for model in spec.models:
            list_page = _flp(model.name, spec)
            route_dir = list_page.lstrip("/")
            _action_paths.add(f"app/{route_dir}/actions.ts")
        files.extend(sorted(_action_paths))
    except Exception:
        # Fallback route-based si dev_actions_generator non disponible
        _planner_actions: set[str] = set()
        for route in spec.routes:
            method = (route.method or "").upper()
            path = route.path or ""
            is_webhook = "webhook" in path.lower() or "stripe" in path.lower()
            if not is_webhook and method in ("POST", "PUT", "PATCH", "DELETE"):
                clean = path.lstrip("/")
                if clean.startswith("api/"):
                    clean = clean[4:]
                seg = clean.split("/")[0] if clean else ""
                if seg:
                    _planner_actions.add(f"app/{seg}/actions.ts")
        files.extend(sorted(_planner_actions))

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

    # pages-client : pour chaque page [INTERACTIVE]
    pages_detail = getattr(spec, "pages_detail", {}) or {}
    if isinstance(pages_detail, dict):
        for path, detail in pages_detail.items():
            if "[INTERACTIVE]" in str(detail):
                page_slug = path.strip("/")
                client_file = (
                    f"app/{page_slug}/page-client.tsx"
                    if page_slug else "app/page-client.tsx"
                )
                files.append(client_file)

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
    Construit le system prompt compact pour le dev agent v4 — Option A (Phase-Aware).

    Phase-Aware : pages_detail et action_map sont EXCLUS du system prompt (trop lourds).
    Ils sont injectés par executor_node via HumanMessage au moment de générer chaque page.
    Budget system prompt visé : ≤ 4 000 tokens.

    Option A :
      - lib/types.ts, lib/schemas.ts, lib/services/*.ts, app/**/actions.ts → PRÉ-GÉNÉRÉS
      - Le LLM génère uniquement : page.tsx (et webhooks/route.ts si présents)
      - service_map : injecté ici (DAL — toujours pertinent)
      - action_map  : injecté par executor_node au moment de chaque page
      - prisma_type_map : DMMF extrait après prisma generate
    """
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
        pre_written_block = f"""
══════════════════════════════════════════════════════════════
FICHIERS PRÉ-GÉNÉRÉS — NE PAS RÉÉCRIRE
══════════════════════════════════════════════════════════════
Ces fichiers sont CORRECTS et COMPLETS — ne les réécrits JAMAIS :
{pre_written_list}
"""

    return f"""Tu génères un projet Next.js 14 complet avec Clerk V6 + Prisma 7 — OPTION A.
{mandatory_rag_block}
Tu as accès à des outils Python pour écrire des fichiers, exécuter des commandes shell, et rechercher des standards.

ARCHITECTURE OPTION A :
  - lib/types.ts, lib/schemas.ts, lib/services/*.ts, app/**/actions.ts → DÉJÀ GÉNÉRÉS (ne pas réécrire)
  - Tu génères UNIQUEMENT : app/**/page.tsx (Server Components) et webhooks si présents
  - Les mutations passent par des Server Actions PRÉ-GÉNÉRÉES — IMPORTER depuis './actions', NE PAS recréer
  - Les pages lisent les données VIA LE SERVICE : xxxService.getAll(userId) — JAMAIS prisma directement dans page.tsx
{service_map_block}{dmmf_block}{pre_written_block}
══════════════════════════════════════════════════════════════
SPEC — SOURCE DE VÉRITÉ (NE PAS MODIFIER LES NOMS)
══════════════════════════════════════════════════════════════
{spec_json}

PAGES À CRÉER :
{pages_summary}

ROUTES API (webhooks seulement) :
{routes_summary}

══════════════════════════════════════════════════════════════
SCHÉMA PRISMA EXACT (déjà écrit dans prisma/schema.prisma — NE PAS RÉÉCRIRE)
══════════════════════════════════════════════════════════════
{prisma_block}
⚠️  Chaque appel prisma.X doit correspondre à un modèle ci-dessus.
    Ne jamais inventer prisma.audit, prisma.booking si non déclaré.

══════════════════════════════════════════════════════════════
FICHIERS À GÉNÉRER PAR LE LLM (checklist — génère-les tous)
══════════════════════════════════════════════════════════════
{files_checklist}

══════════════════════════════════════════════════════════════
TES OUTILS
══════════════════════════════════════════════════════════════
write_file(path, content)             → écrire un fichier (contenu brut, jamais de balises markdown)
read_file(path)                       → aperçu 30 lignes
read_file(path, start_line, end_line) → plage précise de lignes
list_directory(path)                  → lister un dossier
shell_exec(command)                   → commande shell
file_exists(path)                     → EXISTS ou ABSENT
web_search(query)                     → recherche doc/fix TypeScript ou Next.js — utilise UNIQUEMENT si bloqué après 1-2 tentatives de correction infructueuses — formule une requête ciblée : code TS + message d'erreur + stack (ex: "TS2322 null not assignable undefined props Next.js 14 fix")

══════════════════════════════════════════════════════════════
WORKFLOW (Option A — suis cet ordre STRICTEMENT)
══════════════════════════════════════════════════════════════
1. Les fichiers PRÉ-GÉNÉRÉS suivants sont VERROUILLÉS — NE PAS LES RÉÉCRIRE :
   - app/**/actions.ts       : Server Actions CRUD déterministes
   - app/**/page.tsx         : Server Components avec data-fetching déterministe
     ↳ Ces fichiers passent déjà <XxxClient items={items} /> au Client Component.
     ↳ Ne PAS modifier le nom du prop (toujours `items`), ne PAS recréer page.tsx.
   - lib/services/*.service.ts, lib/types.ts, prisma/schema.prisma : idem

2. Les fichiers page-client.tsx sont PRÉ-SCAFFOLDÉS avec l'interface props correcte.
   NE PAS modifier l'interface existante — compléter UNIQUEMENT le JSX body.
   Exemple : si tu trouves `interface DashboardClientProps { items: SerializedPost[] }`,
   le composant DOIT accepter `{{ items }}: DashboardClientProps` — ne pas changer en `{{}}`.
   Pour les pages [INTERACTIVE] : le Client Component (page-client.tsx) importe les Server Actions
   depuis './actions' — le chemin d'import exact et les signatures sont injectés au moment de générer ce fichier.

3. Génère les pages (app/**/page.tsx) — uniquement celles SANS `model` (non verrouillées) :
   - Server Component (pas de 'use client' sauf si interaction pure)
   - JAMAIS prisma directement dans page.tsx — import {{ xxxService }} from '@/lib/services/xxx.service'
   - NE PAS appeler .toISOString() sur les données du service — les dates sont déjà string (SerializedXxx)

   PAGES PROTÉGÉES (auth_required = true) :
   - const {{ userId }} = await auth(); if (!userId) redirect('/sign-in');
   - Lit les données VIA LE SERVICE : `const items = await xxxService.getAll(userId)`
   - Pour les pages dynamiques [id] : `const item = await xxxService.getById(userId, params.id)`
     ↳ getById appelle notFound() automatiquement si absent → NE PAS ajouter de null-check
     ↳ item est toujours SerializedXxx après getById — pas de `| null`, pas d'import notFound

   PAGES PUBLIQUES (marquées "(publique)" dans la liste des pages) :
   - NE PAS importer auth, NE PAS appeler auth(), NE PAS appeler redirect('/sign-in')
   - NE PAS utiliser userId — il n'existe pas sur ces pages
   - Utilise la méthode sans userId du service (ex: xxxService.getPublished() si disponible dans la Service Map)
   - Si aucune méthode sans userId n'existe dans la Service Map → génère juste le JSX sans fetch de données
   - Si [INTERACTIVE] → split Server/Client avec page-client.tsx
   - Client Component navigation : TOUJOURS useRouter depuis 'next/navigation' — JAMAIS 'next/router' (Pages Router)
     ✅  import {{ useRouter }} from 'next/navigation'   → router.refresh() disponible
     ❌  import {{ useRouter }} from 'next/router'       → INTERDIT (App Router) + router.refresh() absent → TS2339

4. Si webhooks présents → génère app/api/webhooks/**/route.ts

5. Lance le build :
   shell_exec('npm run build')
   - Build success (OK en préfixe) → terminé
   - Build échoué → lis l'erreur, corriger, rebuild (max 3 tentatives)
   - Si erreur tsc → shell_exec('npx tsc --noEmit') puis corriger

══════════════════════════════════════════════════════════════
RÈGLE ABSOLUE — APPEL SERVER ACTION DEPUIS CLIENT COMPONENT
══════════════════════════════════════════════════════════════
create/update attendent `formData: FormData` — PAS un objet plain.
delete attend `id: string` — PAS FormData.

Appels corrects depuis un Client Component :
  ✅  create/update :
      const fd = new FormData()
      fd.set('name', nameValue)
      await createXxx(fd)
  ✅  delete :
      await deleteXxx(item.id)   ← id string direct, PAS new FormData()
  ❌  await createXxx({{ name: nameValue }})   ← TS2353 fatal (objet ≠ FormData)
  ❌  await deleteXxx(new FormData(...))     ← TS2345 fatal (FormData ≠ string)

══════════════════════════════════════════════════════════════
RÈGLE ABSOLUE — TYPES PROPS CLIENT COMPONENTS (champs nullable Prisma)
══════════════════════════════════════════════════════════════
Prisma retourne string | null pour les champs optionnels (String? dans le schéma).
Dans les interfaces props de Client Components, utiliser string | null, JAMAIS string | undefined :
  ✅  description?: string | null   ← compatible avec Prisma (TS2322 évité)
  ❌  description?: string          ← refuse null → TS2322 fatal
  ❌  description?: string | undefined  ← idem, refuse null
Règle : pour CHAQUE champ nullable dans les props → ajouter | null explicitement.

══════════════════════════════════════════════════════════════
RÈGLE ABSOLUE — DÉCOUPAGE page.tsx / page-client.tsx
══════════════════════════════════════════════════════════════
Ne JAMAIS créer page-client.tsx SAUF si la page est marquée [INTERACTIVE].

Pour pages NON [INTERACTIVE] :
  ✅  'use client' directement en ligne 1 de page.tsx si onClick/useState requis
  ❌  JAMAIS page-client.tsx sans marquage explicite [INTERACTIVE]

Si [INTERACTIVE] :
  ✅  import XxxClient from './page-client'    ← DEFAULT import
  ❌  import {{ XxxClient }} from './page-client'  ← INTERDIT TS2614

══════════════════════════════════════════════════════════════
RÈGLE ABSOLUE — SÉRIALISATION DATES PRISMA
══════════════════════════════════════════════════════════════
CAS 1 — Données lues via le service (getAll, getById, getAllWithRelations) :
  Le service sérialise les DateTime en string via _serialize — type de retour SerializedXxx.
  ✅  const items = await xxxService.getAll(userId)   ← items[0].createdAt est déjà string
  ❌  items.map(i => ({{ ...i, createdAt: i.createdAt.toISOString() }}))  ← TS2551 fatal
  Les props Client Components qui reçoivent ces données utilisent SerializedXxx ou string pour les dates.

CAS 2 — Server Action reçoit une date string → z.coerce.date() dans le schéma la coerce en Date
  parsed.data.dateField est déjà un Date — passer directement au service, pas de new Date() dans les actions

CAS 3 — Rendu JSX direct :
  ✅  {{item.createdAt}}  ← déjà string (SerializedXxx)
  ❌  {{item.createdAt.toISOString()}}  ← TS2551 si item vient du service

{stack_rules_block}
""".replace("{WORKDIR}", "/app/generated-projects")
