"""
scripts/validate_config_consumption.py — Sprint 3.

Détecte les Config-Runtime Drifts : champs déclarés dans un fichier JSON stack
mais jamais lus par le code runtime (agents/, shared_tools.py, dev.py, etc.).

Usage:
  python scripts/validate_config_consumption.py [--stack nextjs-clerk-prisma]

Sortie:
  rapport JSON + tableau texte {champ: "consumed" | "DRIFT"}

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
# Format : "json_key": [regex1, regex2, ...]  (au moins un doit matcher)
FIELD_PATTERNS: dict[str, list[str]] = {
    "root_file":            [r'get_root_file', r'"root_file"'],
    "primary_manifest":     [r'get_root_file', r'primary_manifest'],
    "commands":             [r'get_commands', r'cmds\.get'],
    "qdrant_filter":        [r'get_qdrant_filter_cfg', r'_build_rag_filter'],
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
}

# Répertoires du code runtime à scanner
RUNTIME_DIRS = [
    Path("agents"),
    Path("workflows"),
    Path("run"),
]

# Extensions à scanner
CODE_EXTENSIONS = {".py"}


def _collect_runtime_source(base: Path) -> str:
    """Concatène tout le code runtime en une seule string pour le grep."""
    parts: list[str] = []
    for runtime_dir in RUNTIME_DIRS:
        scan_dir = base / runtime_dir
        if not scan_dir.exists():
            continue
        for path in scan_dir.rglob("*"):
            if path.suffix in CODE_EXTENSIONS and path.is_file():
                try:
                    parts.append(path.read_text(encoding="utf-8", errors="ignore"))
                except Exception:
                    pass
    return "\n".join(parts)


def _check_field(field: str, patterns: list[str], source: str) -> str:
    """Retourne 'consumed' si au moins un pattern matche, 'DRIFT' sinon."""
    for pat in patterns:
        if re.search(pat, source):
            return "consumed"
    return "DRIFT"


def main() -> int:
    parser = argparse.ArgumentParser(description="Détecte les Config-Runtime Drifts")
    parser.add_argument(
        "--stack",
        default="nextjs-clerk-prisma",
        help="Stack ID à analyser (ex: nextjs-clerk-prisma)",
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
    source = _collect_runtime_source(base)

    results: dict[str, str] = {}
    drifts: list[str] = []

    for field in FIELD_PATTERNS:
        if field not in stack_cfg:
            results[field] = "not_declared"
            continue
        status = _check_field(field, FIELD_PATTERNS[field], source)
        results[field] = status
        if status == "DRIFT":
            drifts.append(field)

    if args.json:
        print(json.dumps({"stack": args.stack, "results": results, "drifts": drifts}, indent=2))
        return 1 if drifts else 0

    # Affichage tableau texte
    print(f"\n{'='*60}")
    print(f"  Config-Runtime Drift Report — stack: {args.stack}")
    print(f"{'='*60}")
    max_len = max(len(f) for f in results)
    for field, status in results.items():
        icon = "✅" if status == "consumed" else ("⚠️ " if status == "not_declared" else "❌")
        print(f"  {icon} {field:<{max_len}}  {status}")
    print(f"{'='*60}")

    if drifts:
        print(f"\n  ❌ {len(drifts)} DRIFT(S) DÉTECTÉ(S): {', '.join(drifts)}")
        print("  → Ajouter le field au code runtime ou retirer du JSON.\n")
        return 1

    print(f"\n  ✅ Aucun drift — tous les champs déclarés sont consommés.\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
