"""
cleanup_generated.py — Supprime tous les fichiers générés par le pipeline lors des runs.
Usage : python scripts/cleanup_generated.py
        python scripts/cleanup_generated.py --dry-run   (simulation sans suppression)

AVERTISSEMENT : Outil de développement local UNIQUEMENT.
- Ne jamais appeler depuis un workflow Temporal ou un agent automatisé.
- Supprime définitivement app/, src/, prisma/, tests générés et tous les logs de runs.
- Utiliser --dry-run pour vérifier ce qui sera supprimé avant d'agir.
- En production, les projets générés vivent dans le volume Docker FACTORY_WORKDIR,
  qui dispose de son propre cycle de vie (ne pas gérer via ce script).
"""
import argparse
import glob
import os
import shutil
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# --- Dossiers générés (Next.js app, src, prisma, mocks, tests générés) ---
GENERATED_DIRS = [
    "app",
    "src",
    "prisma",
    "__mocks__",
    "tests/app",
    "tests/src",
    "tests/pages",
    "tests/config",
]

# --- Fichiers générés à la racine ---
GENERATED_FILES = [
    "package.json",
    "middleware.ts",
    "tsconfig.json",
    "jest.config.js",
    "jest.setup.js",
    ".eslintrc.json",
    # FrontendActivity (Sprint 4.9A)
    "tailwind.config.js",
    "postcss.config.js",
    # Tests générés hors sous-dossiers
    "tests/middleware.test.ts",
    "tests/jestConfig.test.js",
    "tests/jestSetup.test.js",
    "tests/babelrc.test.js",
    "tests/jest.config.test.js",
    "tests/jest.setup.test.js",
    "tests/tsconfig.test.ts",
]

# --- Logs de runs (glob) ---
GENERATED_GLOBS = [
    "logs/metrics/todo_pilot_batch_*.json",
    "logs/metrics/rag_usage*.jsonl",
    "logs/shadow/learner_shadow_log.json",
    "logs/shadow/patterns_report.json",
    "logs/learner_suggestions.json",
    "logs/run_reports/*.md",
    "snapshots/*.json",
    "generated-projects/**",
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true",
                        help="Affiche ce qui serait supprimé sans supprimer")
    args = parser.parse_args()
    dry = args.dry_run

    if dry:
        print("=== DRY RUN — aucun fichier supprimé ===\n")
    else:
        print("=== NETTOYAGE des fichiers générés ===\n")

    deleted = 0
    kept = 0

    # Dossiers
    for d in GENERATED_DIRS:
        full = os.path.normpath(os.path.join(BASE, d))
        if os.path.isdir(full):
            print(f"  [DIR]  {d}")
            if not dry:
                shutil.rmtree(full)
            deleted += 1
        else:
            kept += 1

    # Fichiers explicites
    for f in GENERATED_FILES:
        full = os.path.normpath(os.path.join(BASE, f))
        if os.path.isfile(full):
            print(f"  [FILE] {f}")
            if not dry:
                os.remove(full)
            deleted += 1
        else:
            kept += 1

    # Globs
    for pattern in GENERATED_GLOBS:
        for full in glob.glob(os.path.join(BASE, pattern), recursive=True):
            rel = os.path.relpath(full, BASE)
            if os.path.isfile(full):
                print(f"  [LOG]  {rel}")
                if not dry:
                    os.remove(full)
                deleted += 1

    print(f"\n{'[DRY RUN] ' if dry else ''}Supprimés: {deleted} | Déjà absents: {kept}")
    if not dry:
        print("Nettoyage terminé.")


if __name__ == "__main__":
    main()
