"""
scripts/validate_config_consumption.py — Sprint 3/4.

Détecte les Config-Runtime Drifts : champs déclarés dans un fichier JSON stack
mais jamais lus par le code runtime (agents/, shared_tools.py, dev.py, etc.).

Usage:
  python scripts/validate_config_consumption.py [--stack nextjs-clerk-prisma]
  python scripts/validate_config_consumption.py --component dev_test_activity
  python scripts/validate_config_consumption.py --json

Sortie:
  rapport texte par composant + tableau {champ: "consumed by <file>" | "DRIFT"}

Différence avec validate_contracts.py:
  validate_contracts          = "le JSON est-il bien écrit ?"
  validate_config_consumption = "le JSON est-il bien utilisé ?"
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# Champs déclarés dans le JSON stack → patterns Python attendus dans le code runtime
# Format : "json_key": [regex1, regex2, ...]  (au moins un doit matcher dans au moins un fichier)
FIELD_PATTERNS: dict[str, list[str]] = {
    "root_file":            [r'get_root_file', r'"root_file"'],
    "primary_manifest":     [r'get_root_file', r'primary_manifest'],
    "commands":             [r'get_commands', r'cmds\.get'],
    "qdrant_filter":        [r'get_qdrant_filter_cfg', r'_build_rag_filter', r'_build_architect_rag_filter'],
    "cleanup_artifacts":    [r'get_cleanup_artifacts'],
    "workdir_keep_extra":   [r'get_workdir_keep_extra'],
    "packages":             [r'packages\.items\(\)', r'"packages"'],
    "dev_packages":         [r'dev_packages'],
    "forbidden_imports":    [r'forbidden_imports'],
    "forbidden_keywords":   [r'forbidden_keywords'],
    "import_remaps":        [r'import_remaps', r'_apply_import_remaps'],
    "templated_files":      [r'templated_files'],
    "blueprint":            [r'get_blueprint', r'blueprint'],
    "mandatory_rag_queries":[r'mandatory_rag_queries'],
    "prompt_rules":         [r'prompt_rules'],
    "compatibility_matrix": [r'compatibility_matrix'],
    "spec_validation":      [r'spec_validation'],
    # Sprint 4 — nouveaux champs consommés
    "env_validation":       [r'env_validation', r'env_cfg', r'required_vars'],
    "extraction_rules":     [r'extraction_rules'],
}

# Répertoires du code runtime à scanner
RUNTIME_DIRS = [
    Path("agents"),
    Path("workflows"),
    Path("run"),
]

# Extensions à scanner
CODE_EXTENSIONS = {".py"}


def _collect_runtime_files(base: Path) -> dict[str, str]:
    """Retourne un dict {chemin_relatif: contenu} pour tous les fichiers runtime."""
    files: dict[str, str] = {}
    for runtime_dir in RUNTIME_DIRS:
        scan_dir = base / runtime_dir
        if not scan_dir.exists():
            continue
        for path in scan_dir.rglob("*"):
            if path.suffix in CODE_EXTENSIONS and path.is_file():
                try:
                    rel = str(path.relative_to(base))
                    files[rel] = path.read_text(encoding="utf-8", errors="ignore")
                except Exception:
                    pass
    return files


def _check_field_by_component(
    field: str, patterns: list[str], runtime_files: dict[str, str]
) -> tuple[str, list[str]]:
    """
    Vérifie la consommation d'un champ fichier par fichier.
    Retourne (status, consuming_components) où status = "consumed" | "DRIFT".
    """
    consumers: list[str] = []
    for filepath, content in runtime_files.items():
        for pat in patterns:
            if re.search(pat, content):
                consumers.append(filepath)
                break
    if consumers:
        return "consumed", consumers
    return "DRIFT", []


def main() -> int:
    parser = argparse.ArgumentParser(description="Détecte les Config-Runtime Drifts par composant")
    parser.add_argument(
        "--stack",
        default="nextjs-clerk-prisma",
        help="Stack ID à analyser (ex: nextjs-clerk-prisma)",
    )
    parser.add_argument(
        "--component",
        default="",
        help="Filtrer le rapport sur un composant (ex: dev_test_activity)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Sortie JSON machine-readable",
    )
    args = parser.parse_args()

    base = Path(__file__).parent.parent
    stack_path = base / "config" / "stacks" / f"{args.stack}.json"

    if not stack_path.exists():
        print(f"ERREUR: Stack config introuvable: {stack_path}", file=sys.stderr)
        return 1

    stack_cfg = json.loads(stack_path.read_text(encoding="utf-8"))
    runtime_files = _collect_runtime_files(base)

    if args.component:
        runtime_files = {k: v for k, v in runtime_files.items() if args.component in k}
        if not runtime_files:
            print(f"[!] Aucun fichier trouvé pour le composant '{args.component}'", file=sys.stderr)
            return 1

    results: dict[str, dict] = {}
    drifts: list[str] = []

    for field, patterns in FIELD_PATTERNS.items():
        if field not in stack_cfg:
            results[field] = {"status": "not_declared", "consumed_by": []}
            continue
        status, consumers = _check_field_by_component(field, patterns, runtime_files)
        results[field] = {"status": status, "consumed_by": consumers}
        if status == "DRIFT":
            drifts.append(field)

    if args.json:
        print(json.dumps({"stack": args.stack, "component_filter": args.component, "results": results, "drifts": drifts}, indent=2))
        return 1 if drifts else 0

    # Affichage tableau texte par composant
    print(f"\n{'='*70}")
    print(f"  Config-Runtime Drift Report — stack: {args.stack}", end="")
    if args.component:
        print(f"  (composant: {args.component})", end="")
    print(f"\n{'='*70}")
    max_len = max(len(f) for f in results)
    for field, info in results.items():
        status = info["status"]
        consumers = info["consumed_by"]
        if status == "consumed":
            short_consumers = ", ".join(Path(c).name for c in consumers[:3])
            print(f"  OK  {field:<{max_len}}  consumed by: {short_consumers}")
        elif status == "not_declared":
            print(f"  --  {field:<{max_len}}  not declared in stack JSON")
        else:
            print(f"  !!  {field:<{max_len}}  DRIFT")
    print(f"{'='*70}")

    if drifts:
        print(f"\n  {len(drifts)} DRIFT(S) DETECTE(S): {', '.join(drifts)}")
        print("  -> Ajouter le field au code runtime ou retirer du JSON.\n")
        return 1

    print(f"\n  OK — aucun drift. Tous les champs declares sont consommes.\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
