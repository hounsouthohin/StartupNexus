"""
scripts/non_couverts.py
───────────────────────
Rassemble les « non couverts » signalés par le miroir (USINE.md, « En continu ») :
ce que les briefs demandaient et que l'usine n'a pas su porter.

Sources :
  - logs/declarations/<projet>/*.json   (chaque run depuis le 30 sept 2026)
  - harness/declarations/*.json         (étalons)
  - logs/run_reports/*.md, logs/metrics/run_reports/*.md  (anciens rapports)

Sortie : logs/non_couverts.md (liste unique, la plus récente par projet en premier).
Le classement par axe viendra avec le nouveau miroir (phase 4).

Usage : python scripts/non_couverts.py
"""
from __future__ import annotations

import json
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
OUTPUT = _ROOT / "logs" / "non_couverts.md"


def _from_declarations() -> list[tuple[str, str, str, str]]:
    """(projet, date, source, texte) depuis les déclarations conservées."""
    rows = []
    paths = sorted((_ROOT / "logs" / "declarations").glob("*/*.json"))
    paths += sorted((_ROOT / "harness" / "declarations").glob("*.json"))
    for path in paths:
        try:
            decl = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        spec = decl.get("project_spec") or {}
        for item in spec.get("unsupported") or []:
            rows.append((
                decl.get("project_name", path.stem),
                str(decl.get("created_at", ""))[:10],
                str(path.relative_to(_ROOT)).replace("\\", "/"),
                str(item).strip(),
            ))
    return rows


def _from_reports() -> list[tuple[str, str, str, str]]:
    """(projet, date, source, texte) depuis les FactoryRunReport .md (format : '  ✗ texte')."""
    rows = []
    for folder in (_ROOT / "logs" / "run_reports", _ROOT / "logs" / "metrics" / "run_reports"):
        for path in sorted(folder.glob("*.md")):
            match = re.match(r"(.+)_(\d{4}-\d{2}-\d{2})$", path.stem)
            project, date = (match.group(1), match.group(2)) if match else (path.stem, "")
            in_section = False
            for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
                if "NON COUVERT" in line:
                    in_section = True
                    continue
                if in_section:
                    if line.strip().startswith("✗ "):
                        rows.append((project, date, str(path.relative_to(_ROOT)).replace("\\", "/"),
                                     line.strip()[2:].strip()))
                    elif line.strip():
                        in_section = False
    return rows


def main() -> int:
    rows = _from_declarations() + _from_reports()
    # Un même texte pour un même projet n'est compté qu'une fois (rapport + déclaration du même run).
    unique: dict[tuple[str, str], tuple[str, str]] = {}
    for project, date, source, text in rows:
        key = (project, text)
        if key not in unique or date > unique[key][0]:
            unique[key] = (date, source)

    by_project: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for (project, text), (date, _source) in unique.items():
        by_project[project].append((date, text))

    lines = [
        "# Non couverts — ce que les briefs demandaient et que l'usine n'a pas su porter",
        "",
        f"Généré le {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')} UTC par `scripts/non_couverts.py`.",
        f"**{len(unique)} demande(s) non couverte(s)** sur **{len(by_project)} projet(s)**.",
        "",
        "> Attention : la plupart de ces briefs ont été écrits par nous. Ce n'est pas encore la",
        "> demande réelle — d'où les vrais briefs (USINE.md, « En continu »).",
        "",
    ]
    for project in sorted(by_project, key=lambda p: max(d for d, _ in by_project[p]), reverse=True):
        items = sorted(by_project[project], reverse=True)
        lines.append(f"## {project} ({len(items)})")
        lines += [f"- {text}" + (f"  _({date})_" if date else "") for date, text in items]
        lines.append("")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"{len(unique)} non couvert(s) sur {len(by_project)} projet(s) → {OUTPUT.relative_to(_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
