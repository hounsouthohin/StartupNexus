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
from typing import TYPE_CHECKING

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


def build_system_prompt(spec: "ProjectSpec", pre_written_files: list[str] | None = None) -> str:
    """
    Construit le system prompt complet pour le dev agent v4.
    Reçoit un ProjectSpec typé — les noms sont garantis exacts.
    pre_written_files : fichiers déjà écrits depuis les templates (le LLM ne doit pas les réécrire).
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

    # Spec JSON compacte pour référence LLM
    spec_json = json.dumps({
        "models": [m.name for m in spec.models],
        "pages": [p.path for p in spec.pages],
        "routes": [f"{r.method} {r.path}" for r in spec.routes],
        "fingerprint": spec.spec_fingerprint,
    }, ensure_ascii=False)

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
Tu as accès à des outils Python pour écrire des fichiers, exécuter des commandes shell, et rechercher des standards.
{pre_written_block}
══════════════════════════════════════════════════════════════
SPEC — SOURCE DE VÉRITÉ (NE PAS MODIFIER LES NOMS)
══════════════════════════════════════════════════════════════
{spec_json}

PAGES À CRÉER :
{pages_summary}

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
read_file(path)             → lire un fichier existant
list_directory(path)        → lister le contenu d'un dossier
shell_exec(command)         → exécuter une commande shell
file_exists(path)           → vérifier si un fichier existe (retourne EXISTS ou ABSENT)
rag_search(query)           → chercher des standards d'implémentation

══════════════════════════════════════════════════════════════
WORKFLOW (suis cet ordre STRICTEMENT)
══════════════════════════════════════════════════════════════
1. Génère les fichiers de la checklist ci-dessus (les templates sont déjà présents)
   - Ne réécris jamais les fichiers pré-générés (incluant prisma/schema.prisma et lib/prisma.ts)
   - Puis app/page.tsx, les autres pages, et les routes API
   - Pour chaque route API : vérifie que le modèle Prisma est dans schema.prisma
   - Pour chaque page : importe uniquement des composants que tu as créés
   - Génère-les TOUS avant d'exécuter la moindre commande shell

1b. Génère le client Prisma (npm install déjà exécuté avant ton démarrage) :
    shell_exec("node_modules/.bin/prisma generate")

2. Vérifie les types TypeScript :
   shell_exec("npx tsc --noEmit")
   - Si erreurs → corrige le fichier EXACT mentionné dans l'erreur, puis revérifie
   - Ne pas lancer npm build tant que tsc --noEmit a des erreurs

3. Lance le build :
   shell_exec("npm run build")
   - Build success (OK en préfixe) → tu as terminé
   - Build échoué (FAILED en préfixe) → lis l'erreur complète, identifie le fichier exact, corrige, rebuild
   - Maximum 3 tentatives de build

{stack_rules_block}
══════════════════════════════════════════════════════════════
RÈGLES ABSOLUES STACK (ne jamais enfreindre)
══════════════════════════════════════════════════════════════
- Utilise EXACTEMENT les noms de la spec (Product pas Produit, /api/products pas /api/items)
- App Router UNIQUEMENT → dossier app/ — jamais pages/
- Auth : Clerk V6 uniquement → import {{ auth, currentUser }} from '@clerk/nextjs/server'
- Pas de bcrypt, jwt, next-auth, passport, oauth dans le code
- ClerkProvider dans app/layout.tsx — OBLIGATOIRE
- middleware.ts : export {{ default }} from '@clerk/nextjs/server' avec clerkMiddleware()
- Chaque modèle Prisma doit avoir : id String @id @default(uuid()), createdAt DateTime @default(now())
- Route handlers App Router : toujours typer les paramètres explicitement :
  `export async function GET(request: NextRequest, {{ params }}: {{ params: {{ id: string }} }}) {{`
  Importer NextRequest : `import {{ NextRequest }} from 'next/server'`
- .env.local : OBLIGATOIRE avec ces valeurs exactes (format requis) :
  NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_placeholder
  CLERK_SECRET_KEY=sk_test_placeholder
  DATABASE_URL=postgresql://user:password@localhost:5432/dbname
- Pas de champ "password" ou "passwordHash" dans schema.prisma
""".replace("{WORKDIR}", "/app/generated-projects")
