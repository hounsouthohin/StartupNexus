"""
scripts/matrix_bench.py
───────────────────────
Banc d'essai de la matrice des capacités (USINE.md, phase 3) : le test « sur papier ».

Pour chaque harness/matrices/<projet>.access.yaml (entrée écrite à la main) :
  1. calcule la matrice (agents/capability_matrix.py), en vérifiant les citations contre le
     brief (harness/declarations/<projet>.json, ou harness/matrices/<projet>.brief.txt) ;
  2. la compare case par case à harness/matrices/<projet>.expected.yaml (écrite AVANT le calcul) ;
  3. affiche les problèmes, les dérivés (menus, tableaux de bord, pages) et le miroir.

Usage :
    python scripts/matrix_bench.py                 # tous les projets, détail complet
    python scripts/matrix_bench.py --only garage-atlas
    python scripts/matrix_bench.py --summary       # récapitulatif seulement
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml
from pydantic import ValidationError

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

from agents.capability_matrix import (  # noqa: E402
    AccessDeclaration, compute_matrix, derive_dashboards, derive_nav, derive_pages, explain, questions,
)

MATRICES = _ROOT / "harness" / "matrices"
DECLARATIONS = _ROOT / "harness" / "declarations"
GREEN, RED, YELLOW, BOLD, DIM, RESET = "\033[32m", "\033[31m", "\033[33m", "\033[1m", "\033[2m", "\033[0m"


def _brief(project: str) -> str | None:
    decl = DECLARATIONS / f"{project}.json"
    if decl.exists():
        return json.loads(decl.read_text(encoding="utf-8")).get("brief", {}).get("description")
    txt = MATRICES / f"{project}.brief.txt"
    return txt.read_text(encoding="utf-8") if txt.exists() else None


def _expected_cell(raw: dict) -> dict:
    """Normalise une case attendue (YAML lit yes/no comme des booléens)."""
    create = raw.get("create", "no")
    if create is True:
        create = "yes"
    elif create is False:
        create = "no"
    return {
        "see": raw.get("see", "none"),
        "see_via": sorted(raw.get("see_via", [])),
        "create": create,
        "edit": bool(raw.get("edit", False)),
        "edit_while": sorted(raw.get("edit_while", [])),
        "delete": bool(raw.get("delete", False)),
        "delete_while": sorted(raw.get("delete_while", [])),
        "transitions": {s: sorted(t) for s, t in (raw.get("transitions") or {}).items()},
    }


def _actual_cell(c) -> dict:
    return {
        "see": c.see, "see_via": sorted(c.see_via), "create": c.create,
        "edit": c.edit, "edit_while": sorted(c.edit_while),
        "delete": c.delete, "delete_while": sorted(c.delete_while),
        "transitions": {s: sorted(t) for s, t in c.transitions.items()},
    }


def _short(c) -> str:
    if c.see == "none":
        return f"via {'+'.join(c.see_via)}" if c.see_via else "—"
    bits = [{"own": "siens", "all": "tout", "published": "publiés"}[c.see]]
    if c.create == "yes":
        bits.append("crée")
    if c.create == "auto":
        bits.append("auto")
    if c.edit:
        bits.append("modifie" + (f"[{'/'.join(c.edit_while)}]" if c.edit_while else ""))
    if c.delete:
        bits.append("supprime" + (f"[{'/'.join(c.delete_while)}]" if c.delete_while else ""))
    if c.transitions:
        bits.append("décide")
    return "·".join(bits)


def run(project: str, summary: bool) -> dict:
    try:
        decl = AccessDeclaration(**yaml.safe_load((MATRICES / f"{project}.access.yaml").read_text(encoding="utf-8")))
    except ValidationError as e:
        print(f"\n{BOLD}▶ {project}{RESET}\n  {RED}entrée refusée{RESET}")
        msgs = [f"{'.'.join(map(str, err['loc']))} : {err['msg']}" for err in e.errors()]
        for msg in msgs:
            print(f"    {RED}•{RESET} {msg}")
        return {"project": project, "exceptions": 0, "diffs": [], "errors": msgs, "warnings": [], "ok": False}
    brief = _brief(project)
    m = compute_matrix(decl, brief=brief)
    result = {"project": project, "exceptions": len(decl.exceptions), "diffs": [], "errors": m.errors,
              "warnings": [i.message for i in m.issues if i.level == "warning"], "limits": []}
    print(f"\n{BOLD}▶ {project}{RESET}" + ("" if brief else f" {YELLOW}(brief introuvable : citations non vérifiées){RESET}"))
    if m.errors:
        for e in m.errors:
            print(f"  {RED}erreur{RESET} {e}")
        result["ok"] = False
        return result

    # Comparaison à l'attendu
    expected_path = MATRICES / f"{project}.expected.yaml"
    if expected_path.exists():
        expected = yaml.safe_load(expected_path.read_text(encoding="utf-8")) or {}
        cells = expected.get("cells") or {}
        for c in m.cells:
            want = _expected_cell((cells.get(c.actor) or {}).get(c.entity) or {})
            got = _actual_cell(c)
            for k in want:
                if want[k] != got[k]:
                    result["diffs"].append(f"{c.actor}/{c.entity}.{k} : attendu {want[k]!r}, calculé {got[k]!r}")
        if "auto_links" in expected and expected["auto_links"] != len(m.auto_links):
            result["diffs"].append(f"liens automatiques : attendu {expected['auto_links']}, calculé {len(m.auto_links)}")
        # Ce que le brief demande et que D1 ne peut pas exprimer : compté, jamais caché.
        result["limits"] = list(expected.get("limites_d1") or [])
    else:
        result["diffs"].append("pas de matrice attendue (expected.yaml absent)")
    result["ok"] = not result["diffs"]

    # Tableau
    width = max(len(e) for e in m.entities) + 2
    print("  " + " " * 16 + "".join(f"{e:<{max(width, 26)}}" for e in m.entities))
    for a in m.actors:
        print(f"  {a:<16}" + "".join(f"{_short(m.cell(a, e)):<{max(width, 26)}}" for e in m.entities))
    if result["diffs"]:
        print(f"  {RED}✗ {len(result['diffs'])} écart(s) avec l'attendu :{RESET}")
        for d in result["diffs"]:
            print(f"    {RED}•{RESET} {d}")
    else:
        print(f"  {GREEN}✓ identique à la matrice attendue{RESET}")
    for i in m.issues:
        color = YELLOW if i.level == "warning" else DIM
        print(f"  {color}{i.level}{RESET} {i.message}")
    for lim in result["limits"]:
        print(f"  {YELLOW}hors D1{RESET} {lim}")
    if summary:
        return result

    for link in m.auto_links:
        print(f"  {DIM}lien auto{RESET} {link}")
    nav, dash = derive_nav(m, decl), derive_dashboards(m, decl)
    print(f"  {BOLD}Menus{RESET}")
    for a, entries in nav.items():
        print(f"    {a:<16} {' · '.join(entries) or '—'}")
    print(f"  {BOLD}Tableaux de bord{RESET}")
    for a, blocks in dash.items():
        print(f"    {a:<16} {' | '.join(blocks) or '—'}")
    print(f"  {BOLD}Pages{RESET}")
    for p in derive_pages(m, decl):
        extra = f" (décision : {', '.join(p.decision_by)})" if p.decision_by else ""
        print(f"    {p.kind:<8} {p.entity or '—':<14} pour {', '.join(p.actors)}{extra}")
    print(f"  {BOLD}Miroir{RESET}")
    for who, lines in explain(m, decl).items():
        for line in lines:
            print(f"    {who} {line}.")
    for q in questions(m, decl):
        print(f"    {YELLOW}?{RESET} {q}")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Banc d'essai de la matrice des capacités")
    parser.add_argument("--only", action="append", default=[])
    parser.add_argument("--summary", action="store_true")
    args = parser.parse_args()

    projects = sorted(p.name[: -len(".access.yaml")] for p in MATRICES.glob("*.access.yaml"))
    if args.only:
        projects = [p for p in projects if p in args.only]
    if not projects:
        print(f"{RED}Aucune entrée dans {MATRICES}{RESET}")
        return 1

    results = [run(p, args.summary) for p in projects]
    print(f"\n{BOLD}═══ Récapitulatif ═══{RESET}")
    for r in results:
        icon = f"{GREEN}✓{RESET}" if r["ok"] else f"{RED}✗{RESET}"
        print(f"  {icon} {r['project']:<20} écarts {len(r['diffs']):<3} exceptions {r['exceptions']:<3} "
              f"alertes {len(r['warnings']):<3} hors D1 {len(r['limits'])}"
              + (f"  {RED}{len(r['errors'])} erreur(s){RESET}" if r["errors"] else ""))
    n = len(results)
    print(f"\n  Exceptions par brief : {sum(r['exceptions'] for r in results) / n:.1f} en moyenne"
          f" · besoins hors D1 : {sum(len(r['limits']) for r in results)}")
    return 0 if all(r["ok"] for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
