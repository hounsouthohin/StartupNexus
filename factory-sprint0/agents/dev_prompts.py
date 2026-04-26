
# agents/dev_prompts.py
"""
System prompt du dev agent v4 (Nouvelle Base — Phase 4A, 28 Mars 2026).

Principe : donner au LLM une boussole claire (objectif, spec, outils, workflow),
pas une prison (gates bloquantes, state machine forcée).

Le LLM sait :
- Ce qu'il doit construire (ProjectSpec — noms exacts)
- Quels fichiers créer (checklist informative)
- Comment utiliser ses outils (write_file, shell_exec, rag_search)
- Son workflow cible (générer → vérifier types → build → corriger si besoin)
- Les règles absolues de la stack (Clerk, App Router, Prisma)
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
    Checklist déterministe des fichiers à générer depuis la ProjectSpec.
    Injectée dans le system prompt comme guide, jamais comme gate bloquante.
    """
    # Base : checklist native du ProjectSpec (pages/routes + coeur minimal).
    files = list(spec.expected_files())

    # Complément stack : blueprint.required_files pour inclure les templates critiques
    # (next.config.js, tsconfig.json, lib/prisma.ts, etc.) sans hardcode.
    try:
        from agents.stack_config import load_stack_config

        stack_id = getattr(spec, "stack_id", "") or "nextjs-clerk-prisma"
        stack_cfg = load_stack_config(stack_id)
        required = stack_cfg.get("blueprint", {}).get("required_files", []) or []
        for path in required:
            if isinstance(path, str) and path.strip():
                files.append(path.strip().replace("\\", "/"))
    except Exception:
        # Non bloquant : si stack_config est indisponible, on conserve la base spec.
        pass

    # Option B : lib/types.ts et lib/services/ générés par le LLM.
    # On les ajoute à la checklist pour qu'il n'oublie pas de les créer.
    import re as _re
    files.append("lib/types.ts")
    for m in spec.models:
        kebab = _re.sub(r"(?<!^)(?=[A-Z])", "-", m.name).lower()
        files.append(f"lib/services/{kebab}.service.ts")

    # pages-client : pour chaque page marquée [INTERACTIVE] dans pages_detail,
    # ajouter le fichier page-client.tsx correspondant à la checklist.
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

    # Déduplique en préservant l'ordre.
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
    du brief. Les standards les plus pertinents sont injectés directement dans le prompt
    — sans attendre que le LLM pense à appeler rag_search.

    Logique de déclenchement (déterministe depuis la spec) :
      - "always"          → toujours (sécurité, fiabilité core)
      - "list-routes"     → si au moins un GET dans spec.routes
      - "relation-models" → si au moins un modèle a un champ *Id (foreign key)
      - "multi-table"     → si spec a 2+ modèles (mutations probables multi-tables)
    """
    try:
        from agents.shared_tools import rag_search as _rag_fn
        from agents.stack_config import load_stack_config
    except Exception:
        return ""  # Qdrant absent → non-bloquant

    # ── Détection des contextes pertinents ───────────────────────────────────
    contexts: list[str] = ["always"]

    has_get_routes = any(r.method == "GET" for r in spec.routes)
    if has_get_routes:
        contexts.append("list-routes")

    has_relations = any(
        any(
            f.name != "id" and f.name.endswith("Id")
            for f in m.fields
        )
        for m in spec.models
    )
    if has_relations:
        contexts.append("relation-models")

    if len(spec.models) >= 2:
        contexts.append("multi-table")

    # "interactive-pages" : toujours déclenché car tout brief avec pages a des boutons CRUD
    if spec.pages:
        contexts.append("interactive-pages")

    # ── Requêtes ciblées par contexte ────────────────────────────────────────
    # Option A — requêtes en anglais technique pour matcher les RULE: des standards reformatés.
    # Les standards commencent maintenant par RULE: <TECHNOLOGIE> (plus ACTION:/STACK: génériques).
    # Ces requêtes ciblent les termes techniques distinctifs qui apparaissent en tête de standard.
    CONTEXT_QUERIES: dict[str, str] = {
        "always":            "auth() userId null guard before Prisma query ownership check CreateInput without userId security logging healthcheck",
        "list-routes":       "pagination findMany skip take PaginatedResponse count $transaction GET list route handler API",
        "relation-models":   "N+1 prevention include select nested relation findUnique loop Promise.all Prisma join",
        "multi-table":       "prisma $transaction sequential interactive rollback multi-table create invoice items atomic",
        "interactive-pages": "'use client' directive useState onClick form handler Client Component interactive Server Component split",
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
            pass  # Qdrant absent → non-bloquant

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
) -> str:
    """
    Construit le system prompt complet pour le dev agent v4.
    Reçoit un ProjectSpec typé — les noms sont garantis exacts.
    pre_written_files : fichiers déjà écrits depuis les templates (le LLM ne doit pas les réécrire).

    Option B (Avril 2026) : lib/types.ts et lib/services/ sont générés par le LLM.
    Le LLM est auteur unique du code applicatif → cohérence garantie, fossé d'auteur éliminé.
    """
    pre_written: set[str] = set(pre_written_files or [])
    expected_files = _expected_files_from_spec(spec)
    # Checklist : seuls les fichiers que le LLM doit GÉNÉRER (pas les templates déjà écrits)
    files_to_generate = [f for f in expected_files if f not in pre_written]
    files_checklist = "\n".join(f"  - {f}" for f in files_to_generate)

    # Règles stack depuis rules_dev.md — source de vérité technique (prisma singleton, auth guard, etc.)
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
        pass  # Non bloquant

    # Bloc Prisma schema attendu — critique pour éviter les modèles fantômes
    prisma_block = spec.to_prisma_schema_block()

    # Résumé des routes pour référence rapide
    routes_summary = "\n".join(
        f"  - {r.method} {r.path}"
        for r in spec.routes
    )

    # Pages
    pages_summary = "\n".join(
        f"  - {p.path}{' (publique)' if not p.auth_required else ''}"
        for p in spec.pages
    )

    # pages_detail — instructions d'affichage précises pour chaque page
    # Sans ce bloc, le LLM invente le contenu des pages au lieu de suivre le brief.
    # Les pages marquées [INTERACTIVE] reçoivent une instruction explicite de split Server+Client.
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
                    f"\n    ⚠️  IMPORT DANS page.tsx (OBLIGATOIRE — DEFAULT import, pas named) :\n"
                    f"      ✅  import {comp_name}Client from './page-client'    ← CORRECT\n"
                    f"      ❌  import {{ {comp_name}Client }} from './page-client'  ← INTERDIT — TS2614\n"
                    f"\n    ⚠️  EXPORT dans {client_file} (OBLIGATOIRE — DEFAULT export) :\n"
                    f"      ✅  export default function {comp_name}Client({{ ... }}: {comp_name}ClientProps) {{ ... }}\n"
                    f"      ❌  export function {comp_name}Client  ← INTERDIT — named export incompatible\n"
                    f"\n    ⚠️  TYPAGE OBLIGATOIRE des props (TS7031 sinon) :\n"
                    f"      interface {comp_name}ClientProps {{ /* props passées par le Server Component */ }}\n"
                    f"      Ne jamais écrire function Comp({{ prop }}) sans interface de props déclarée."
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

    # Bloc services DAL — noms exacts des services à créer (un par modèle métier).
    # Le LLM génère ces fichiers lui-même (Option B) — on lui donne uniquement les noms
    # pour qu'il n'invente pas de variantes (getExpenses, getAllTasks...).
    _service_names = []
    for m in spec.models:
        import re as _re
        kebab = _re.sub(r"(?<!^)(?=[A-Z])", "-", m.name).lower()
        camel = m.name[0].lower() + m.name[1:] if m.name else m.name
        owner = getattr(m, "owner_field", "userId")
        _service_names.append((m.name, camel + "Service", f"lib/services/{kebab}.service.ts", owner))

    services_block = ""
    if _service_names:
        lines = "\n".join(
            f"  {name} → {svc_obj}  ({path})  [owner_field: {owner}]"
            for name, svc_obj, path, owner in _service_names
        )
        services_block = f"""
══════════════════════════════════════════════════════════════
SERVICES DAL À CRÉER (Rule 26 — un par modèle métier)
══════════════════════════════════════════════════════════════
{lines}

owner_field = champ d'ownership du modèle dans le schéma Prisma.
  - userId/authorId → ownership direct : utilise ce champ dans findMany/findUnique/create/update/delete
  - xxxId (ex: boardId) → modèle enfant : utilise l'id du parent comme filtre, vérifie l'ownership du parent dans la route API

Convention fixe — JAMAIS de fonctions nommées exportées :
  ✅  import {{ modelService }} from '@/lib/services/model.service'
  ✅  const items = await modelService.findMany(userId)
  ❌  import {{ getItems, getItemById }} from '@/lib/services/model.service'

Types d'entrée dans lib/types.ts — CreateXxxInput DOIT inclure TOUS les champs mutables :
  ✅  interface CreateLeaveRequestInput {{ startDate: Date; endDate: Date; status?: LeaveStatus; reason?: string }}
  ❌  interface CreateLeaveRequestInput {{ startDate: Date; endDate: Date }}  ← manque status → TS2353
  Règle : pour chaque champ du modèle Prisma (hors id, createdAt, updatedAt), ajouter le champ
  correspondant dans CreateXxxInput (obligatoire si @required, optionnel si nullable/default).
"""

    # Spec JSON compacte pour référence LLM
    spec_json = json.dumps({
        "models": [m.name for m in spec.models],
        "pages": [p.path for p in spec.pages],
        "routes": [f"{r.method} {r.path}" for r in spec.routes],
        "fingerprint": spec.spec_fingerprint,
    }, ensure_ascii=False)

    # ── Bloc RAG obligatoire spec-aware ──────────────────────────────────────
    # Requêtes Qdrant déclenchées AVANT la génération selon le contenu du brief.
    # Garantit que les standards qualité (pagination, N+1, transactions) sont
    # visibles dans le prompt — sans dépendre de l'initiative du LLM.
    mandatory_rag_block = _build_mandatory_rag_block(spec)

    # Bloc fichiers pré-générés (affiché uniquement si la liste est non vide)
    pre_written_block = ""
    if pre_written:
        pre_written_list = "\n".join(f"  - {f}" for f in sorted(pre_written))
        pre_written_block = f"""
══════════════════════════════════════════════════════════════
FICHIERS PRÉ-GÉNÉRÉS — NE PAS RÉÉCRIRE
══════════════════════════════════════════════════════════════
Ces fichiers ont été générés automatiquement depuis les templates de la stack.
Ils sont CORRECTS et COMPLETS — ne les réécrits JAMAIS avec write_file :
{pre_written_list}
"""

    return f"""Tu génères un projet Next.js 14 complet avec Clerk V6 + Prisma 7.
{mandatory_rag_block}
Tu as accès à des outils Python pour écrire des fichiers, exécuter des commandes shell, et rechercher des standards.
{services_block}{pre_written_block}
══════════════════════════════════════════════════════════════
SPEC — SOURCE DE VÉRITÉ (NE PAS MODIFIER LES NOMS)
══════════════════════════════════════════════════════════════
{spec_json}

PAGES À CRÉER :
{pages_summary}
{pages_detail_block}
ROUTES API À CRÉER :
{routes_summary}

══════════════════════════════════════════════════════════════
SCHÉMA PRISMA EXACT (copie-le tel quel dans prisma/schema.prisma)
══════════════════════════════════════════════════════════════
{prisma_block}
⚠️  Chaque route qui appelle `prisma.X` DOIT avoir le modèle X dans ce schéma.
    Ne jamais appeler `prisma.audit`, `prisma.booking` etc. si le modèle n'est pas ci-dessus.

══════════════════════════════════════════════════════════════
FICHIERS À GÉNÉRER PAR LE LLM (checklist — génère-les tous)
══════════════════════════════════════════════════════════════
{files_checklist}

══════════════════════════════════════════════════════════════
TES OUTILS
══════════════════════════════════════════════════════════════
write_file(path, content)   → écrire un fichier (contenu brut UNIQUEMENT — jamais de ```json, ```tsx ou autre balise markdown)
read_file(path)                      → métadonnées + aperçu 30 lignes (pour découvrir un fichier)
read_file(path, start_line, end_line) → lire une plage précise de lignes
list_directory(path)        → lister le contenu d'un dossier
shell_exec(command)         → exécuter une commande shell
file_exists(path)           → vérifier si un fichier existe (retourne EXISTS ou ABSENT)
rag_search(query)           → chercher des standards d'implémentation

══════════════════════════════════════════════════════════════
WORKFLOW (suis cet ordre STRICTEMENT)
══════════════════════════════════════════════════════════════
1. Génère les fichiers dans cet ordre :
   a. lib/types.ts — types partagés (modèles Prisma re-exportés, CreateXxxInput, ApiResponse<T>)
   b. lib/services/<model>.service.ts — un par modèle (voir bloc SERVICES DAL ci-dessus, Rule 26)
   c. app/api/**/route.ts — routes API (peuvent importer prisma directement)
   d. app/**/page.tsx — pages (importent les services via l'objet service, jamais prisma directement)

   ⚠️  STUBS page.tsx PRÉ-GÉNÉRÉS : avant de générer chaque page.tsx, appelle
       read_file("app/<path>/page.tsx") — un stub avec les imports requis a déjà été
       écrit. Lis-le, puis écris la version complète en CONSERVANT TOUS LES IMPORTS
       déjà présents (auth, redirect, notFound). Ne jamais supprimer un import
       existant dans un stub.

   - Ne réécris jamais les fichiers pré-générés (prisma/schema.prisma, lib/prisma.ts)
   - Génère-les TOUS avant d'exécuter la moindre commande shell

1b. Génère le client Prisma OBLIGATOIRE — sans cette étape tsc échouera avec "PrismaClient introuvable" :
    shell_exec("npx prisma generate")
    ⚠️  Si la commande retourne FAILED → lis l'erreur et corrige schema.prisma avant de continuer.
    ⚠️  Ne JAMAIS passer à l'étape 2 si prisma generate a échoué.

2. Vérifie les types TypeScript :
   shell_exec("npx tsc --noEmit")
   - Si erreurs → lis la zone concernée avec read_file(fichier, ligne_erreur-5, ligne_erreur+20), corrige, puis revérifie
   - Ne pas lancer npm build tant que tsc --noEmit a des erreurs

3. Lance le build :
   shell_exec("npm run build")
   - Build success (OK en préfixe) → tu as terminé
   - Build échoué (FAILED en préfixe) → lis l'erreur, identifie fichier + numéro de ligne, appelle read_file(fichier, ligne-5, ligne+20), corrige, rebuild
   - Maximum 3 tentatives de build

══════════════════════════════════════════════════════════════
RÈGLE ABSOLUE — DÉCOUPAGE page.tsx / page-client.tsx
══════════════════════════════════════════════════════════════
Ne JAMAIS créer de fichier page-client.tsx SAUF si la page est explicitement
marquée [INTERACTIVE] dans les instructions CONTENU ATTENDU PAR PAGE ci-dessus.

Pour toute page NON marquée [INTERACTIVE] :
  ✅  Inclure 'use client' directement en ligne 1 de page.tsx si des onClick/useState sont nécessaires
  ❌  JAMAIS générer un page-client.tsx parce que la page semble interactive — TS2307/TS2614

Si la page EST marquée [INTERACTIVE], le seul import autorisé dans page.tsx est :
  ✅  import XxxClient from './page-client'        ← DEFAULT import (sans accolades)
  ❌  import {{ XxxClient }} from './page-client'   ← INTERDIT — TS2614 (named import sur default export)

══════════════════════════════════════════════════════════════
RÈGLE ABSOLUE — SÉRIALISATION DES DATES PRISMA (3 CAS DISTINCTS)
══════════════════════════════════════════════════════════════
Date Prisma, props Client Component et corps POST sont trois contextes différents.

CAS 1 — Server Component → Client Component :
  Sérialise avant de passer en props ET type l'interface en string (jamais Date) :
  const items = data.map(i => ({{ ...i, createdAt: i.createdAt.toISOString() }}))
  ✅  interface CardProps {{ createdAt: string; }}    ← string dans l'interface
  ❌  interface CardProps {{ createdAt: Date; }}      ← TS2322 (string not assignable to Date)

CAS 2 — Route POST : corps JSON arrive en string → convertir avant d'appeler le service :
  ✅  service.create({{ ...body, startDate: new Date(body.startDate) }})
  ❌  service.create(body)  ← TS2345 si CreateXxxInput.startDate est Date

CAS 3 — Rendu JSX direct dans Server Component :
  ✅  {{item.createdAt.toISOString()}}  ou  {{item.createdAt}}  si déjà string
  ❌  {{item.createdAt}}  si encore objet Date  ← TS2322 (Date not assignable to ReactNode)

{stack_rules_block}
""".replace("{WORKDIR}", "/app/generated-projects")
