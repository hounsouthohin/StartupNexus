
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

    # Server Actions — une par segment de modèle avec mutations
    import re as _re
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
    }

    snippets: list[str] = []
    seen_texts: set[str] = set()

    stack_id = getattr(spec, "stack_id", "nextjs-clerk-prisma")
    try:
        stack_cfg = load_stack_config(stack_id)
        qdrant_filter = stack_cfg.get("qdrant_filter", {}).get("filter", {})
    except Exception:
        qdrant_filter = {}

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


def build_system_prompt(
    spec: "ProjectSpec",
    pre_written_files: list[str] | None = None,
    service_map: str = "",
) -> str:
    """
    Construit le system prompt complet pour le dev agent v4 — Option A.

    Option A :
      - lib/types.ts, lib/schemas.ts, lib/services/*.ts → PRÉ-GÉNÉRÉS (ne pas réécrire)
      - Le LLM génère uniquement : actions.ts, page.tsx, webhooks/route.ts
      - service_map : bloc compact des services disponibles (inject depuis dev_graph)
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

    # pages_detail — instructions d'affichage précises pour chaque page
    pages_detail_block = ""
    if spec.pages_detail and isinstance(spec.pages_detail, dict):
        detail_lines = []
        for path, detail in spec.pages_detail.items():
            detail_str = str(detail).strip()
            if "[INTERACTIVE]" in detail_str:
                page_slug = path.strip("/").replace("/", "-") or "home"
                comp_name = page_slug.title().replace("-", "")
                client_file = (
                    f"app/{path.strip('/')}/page-client.tsx"
                    if path.strip("/") else "app/page-client.tsx"
                )
                detail_str += (
                    f"\n    ⚠️  SPLIT OBLIGATOIRE : créer {client_file} avec '\"use client\"' "
                    f"en ligne 1 pour les boutons/handlers. "
                    f"app/{path.strip('/') + '/' if path.strip('/') else ''}page.tsx reste Server Component "
                    f"(fetch données) et rend <{comp_name}Client ... />."
                    f"\n    ⚠️  IMPORT dans page.tsx (DEFAULT import, pas named) :\n"
                    f"      ✅  import {comp_name}Client from './page-client'\n"
                    f"      ❌  import {{ {comp_name}Client }} from './page-client'  ← INTERDIT TS2614\n"
                    f"\n    ⚠️  EXPORT dans {client_file} (DEFAULT export obligatoire) :\n"
                    f"      ✅  export default function {comp_name}Client({{ ... }}: {comp_name}ClientProps) {{ }}\n"
                    f"      ❌  export function {comp_name}Client  ← INTERDIT\n"
                    f"\n    ⚠️  TYPAGE OBLIGATOIRE des props :\n"
                    f"      interface {comp_name}ClientProps {{ /* props du Server Component */ }}"
                )
            detail_lines.append(f"  {path} :\n    {detail_str}")
        if detail_lines:
            pages_detail_block = (
                "\n══════════════════════════════════════════════════════════════\n"
                "CONTENU ATTENDU PAR PAGE (instructions précises — à implémenter tel quel)\n"
                "══════════════════════════════════════════════════════════════\n"
                + "\n\n".join(detail_lines)
                + "\n"
            )

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
Méthodes : .getAll(userId), .getById(userId, id), .create(userId, data), .update(id, data), .delete(userId, id)
"""

    # Spec JSON compacte
    spec_json = json.dumps({
        "models": [m.name for m in spec.models],
        "pages": [p.path for p in spec.pages],
        "routes": [f"{r.method} {r.path}" for r in spec.routes],
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
  - lib/types.ts, lib/schemas.ts, lib/services/*.ts → DÉJÀ GÉNÉRÉS (ne pas réécrire)
  - Tu génères UNIQUEMENT : app/**/actions.ts, app/**/page.tsx, webhooks si présents
  - Les mutations passent par des Server Actions (jamais app/api/** pour le CRUD)
  - Les pages lisent les données directement avec prisma (pas de fetch vers /api)
{service_map_block}{pre_written_block}
══════════════════════════════════════════════════════════════
SPEC — SOURCE DE VÉRITÉ (NE PAS MODIFIER LES NOMS)
══════════════════════════════════════════════════════════════
{spec_json}

PAGES À CRÉER :
{pages_summary}
{pages_detail_block}
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
rag_search(query)                     → standards d'implémentation Qdrant

══════════════════════════════════════════════════════════════
WORKFLOW (Option A — suis cet ordre STRICTEMENT)
══════════════════════════════════════════════════════════════
1. Génère les Server Actions (app/**/actions.ts) :
   - PREMIERE LIGNE obligatoire : 'use server'
   - Importe { auth } from '@clerk/nextjs/server'
   - Importe { revalidatePath } from 'next/cache'
   - Importe le service depuis '@/lib/services/<model>.service'
   - Importe les schémas depuis '@/lib/schemas'
   - Pattern obligatoire dans chaque action :
       const {{ userId }} = await auth();
       if (!userId) throw new Error('Unauthorized');
       const parsed = CreateXxxSchema.safeParse(data);
       if (!parsed.success) throw new Error(parsed.error.message);
       await xxxService.create(userId, parsed.data);
       revalidatePath('/xxx');

2. Génère les pages (app/**/page.tsx) :
   - Server Component (pas de 'use client' sauf si interaction pure)
   - Lit les données : prisma.xxx.findMany({{ where: {{ userId }} }}) directement
   - Si auth_required : const {{ userId }} = await auth(); if (!userId) redirect('/sign-in');
   - Sérialise les dates Prisma avant Client Components : .toISOString()
   - Si [INTERACTIVE] → split Server/Client avec page-client.tsx

3. Si webhooks présents → génère app/api/webhooks/**/route.ts

4. Lance le build :
   shell_exec('npm run build')
   - Build success (OK en préfixe) → terminé
   - Build échoué → lis l'erreur, corriger, rebuild (max 3 tentatives)
   - Si erreur tsc → shell_exec('npx tsc --noEmit') puis corriger

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
CAS 1 — Server Component → Client Component props :
  const items = data.map(i => ({{ ...i, createdAt: i.createdAt.toISOString() }}))
  interface Props {{ createdAt: string; }}   ← toujours string dans l'interface props

CAS 2 — Server Action reçoit une date string → envoyer string (schemas.ts gère string ISO)
  Les schémas Zod utilisent z.string().datetime() → pas de new Date() dans les actions

CAS 3 — Rendu JSX direct :
  ✅  {{item.createdAt.toISOString()}}  ou  {{item.createdAt}}  si déjà string

{stack_rules_block}
""".replace("{WORKDIR}", "/app/generated-projects")
