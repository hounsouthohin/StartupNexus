
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


def build_system_prompt(
    spec: "ProjectSpec",
    pre_written_files: list[str] | None = None,
    types_exported: list[str] | None = None,
) -> str:
    """
    Construit le system prompt complet pour le dev agent v4.
    Reçoit un ProjectSpec typé — les noms sont garantis exacts.
    pre_written_files : fichiers déjà écrits depuis les templates (le LLM ne doit pas les réécrire).
    types_exported    : liste exacte des symboles exportés par lib/types.ts (depuis TypesFileResult).
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

    # Bloc types.ts — affiché uniquement si lib/types.ts est dans pre_written
    types_block = ""
    if "lib/types.ts" in pre_written:
        # C2 : liste les noms EXACTS exportés pour empêcher les hallucinations (ex: CreatePostInput)
        if types_exported:
            exact_names = ", ".join(types_exported)
            forbidden_examples = [
                n for n in ("CreatePostInput", "CreateUserInput", "CreateItemInput")
                if n not in types_exported
            ]
            forbidden_note = (
                f"\nNOM INTERDITS (non exportés, jamais disponibles) : {', '.join(forbidden_examples)}"
                if forbidden_examples
                else ""
            )
            types_block = f"""
══════════════════════════════════════════════════════════════
lib/types.ts — SOURCE DE VÉRITÉ DES TYPES (PRÉ-GÉNÉRÉ)
══════════════════════════════════════════════════════════════
Le fichier lib/types.ts a été généré automatiquement depuis la spec.
Il exporte EXACTEMENT ces symboles (rien d'autre) :
  {exact_names}
  + ApiResponse<T>, PaginatedResponse<T>, AuthenticatedRequest{forbidden_note}

RÈGLE ABSOLUE : utilise UNIQUEMENT ces noms exacts dans tes imports.
  ✅  import type {{ {", ".join(types_exported[:3])} }} from '@/lib/types'
  ❌  N'invente PAS de noms non listés ci-dessus — tsc échouera avec TS2304/TS2724.

NE JAMAIS réécrire lib/types.ts — il est protégé.
"""
        else:
            types_block = """
══════════════════════════════════════════════════════════════
lib/types.ts — SOURCE DE VÉRITÉ DES TYPES (PRÉ-GÉNÉRÉ)
══════════════════════════════════════════════════════════════
Le fichier lib/types.ts a été généré automatiquement depuis la spec.
Il contient :
  - Les types Prisma re-exportés (depuis @prisma/client)
  - ApiResponse<T> et PaginatedResponse<T> pour toutes les routes API
  - CreateXxxInput / UpdateXxxInput pour chaque modèle (champs éditables)
  - XxxPageParams pour les pages dynamiques ([id])
  - AuthenticatedRequest (userId garanti non-null)

RÈGLE ABSOLUE : importe UNIQUEMENT les symboles listés dans ce fichier — jamais d'autres noms.
  ✅  import type { Task, CreateTaskInput, ApiResponse } from '@/lib/types'
  ❌  import type { CreatePostInput } from '@/lib/types'  ← n'existe PAS → TS2724

NE JAMAIS réécrire lib/types.ts — il est protégé.
"""

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
{types_block}{pre_written_block}
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
read_file(path)                      → métadonnées + aperçu 30 lignes (pour découvrir un fichier)
read_file(path, start_line, end_line) → lire une plage précise de lignes
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

{stack_rules_block}
""".replace("{WORKDIR}", "/app/generated-projects")
