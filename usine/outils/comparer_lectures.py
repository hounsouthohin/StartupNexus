"""Compare, brief par brief, la lecture de gpt-5.5 et celle de la session Claude isolée (0 $, lecture seule).
Usage : python usine/outils/comparer_lectures.py <nom> [<nom> …]   (nom = brief sans « appr- », ex. union-sportive, c2-erp-compta)
        python usine/outils/comparer_lectures.py --claude <nom> …   toutes les lectures Claude d'un brief, côte à côte
        (essai Opus → Sonnet : les lectures d'avant le 15 oct 2026 sont d'Opus, les suivantes de Sonnet)"""
import json, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
RUNS = Path(__file__).resolve().parents[2] / "runs"

def derniere(motif, exclure=None):
    l = sorted(p for p in RUNS.glob(motif) if (p / "99-rapport.json").exists() and not (exclure and exclure in p.name))
    return l[-1] if l else None

def resume(run):
    d = json.loads((run / "lecteurs.json").read_text(encoding="utf-8"))
    r = json.loads((run / "99-rapport.json").read_text(encoding="utf-8"))
    per = (d.get("perimetre") or {})
    return {"perimetre": per.get("perimetre"),
            "acteurs": [a.get("libelle") or a.get("id") for a in ((d.get("acteurs") or {}).get("acteurs") or [])],
            "fiches": [(f.get("nom"), f.get("nature")) for f in ((d.get("fiches") or {}).get("fiches") or [])],
            "circuits": [c.get("fiche") for c in ((d.get("circuits") or {}).get("circuits") or [])],
            "droits": len((d.get("droits") or {}).get("droits") or []),
            "champs": sum(len(f.get("champs", [])) for f in ((d.get("champs") or {}).get("fiches") or [])),
            "propositions": sum(len(f.get("propositions", [])) for f in ((d.get("champs") or {}).get("fiches") or [])),
            "refus": sum(1 for j in d.get("journal", []) if j.get("erreurs")),
            "hors_stock": sorted({h["categorie"] for h in per.get("hors_stock", [])}),
            "verdict": r["verdict"].split(":")[0]}

def toutes_claude(nom):
    runs = sorted(p for p in RUNS.glob(f"*-{nom}-claude-comprendre") if (p / "99-rapport.json").exists())
    if len(runs) < 2:
        print(f"### {nom} : moins de 2 lectures Claude ({len(runs)})"); return
    rs = [resume(p) for p in runs]
    print(f"### {nom}")
    for k in rs[0]:
        if all(r[k] == rs[0][k] for r in rs):
            print(f"    {k:<12} {rs[0][k]}"); continue
        print(f"  ≠ {k}")
        for p, r in zip(runs, rs):
            print(f"      {p.name[:15]} : {r[k]}")

if "--claude" in sys.argv:
    for nom in (a for a in sys.argv[1:] if a != "--claude"):
        toutes_claude(nom)
    sys.exit()

for nom in sys.argv[1:]:
    g, c = derniere(f"*-{nom}-comprendre", exclure="-claude-"), derniere(f"*-{nom}-claude-comprendre")
    if not g or not c:
        print(f"### {nom} : lecture manquante (gpt {bool(g)}, claude {bool(c)})"); continue
    a, b = resume(g), resume(c)
    print(f"### {nom}")
    for k in a:
        print(f"  {'  ' if a[k] == b[k] else '≠ '}{k:<12} gpt : {a[k]}")
        if a[k] != b[k]:
            print(f"    {'':<12} cla : {b[k]}")
