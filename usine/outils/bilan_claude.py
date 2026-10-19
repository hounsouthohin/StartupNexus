"""BILAN de la mesure de la session Claude isolée, face aux critères écrits d'avance (USINE.md, 12 oct)."""
import json, re, sys, unicodedata
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
RUNS = Path(r"C:\Users\BAMBARA Arthur\Desktop\StartupNexus\runs")

def complets(motif):
    return sorted(p for p in RUNS.glob(motif) if (p / "99-rapport.json").exists())

def norm(s):
    s = unicodedata.normalize("NFD", s or "").encode("ascii", "ignore").decode().lower()
    return re.sub(r"(profil|fiche|de|du|des|la|le)", "", re.sub(r"[^a-z]", "", s))

def lire(run):
    d = json.loads((run / "lecteurs.json").read_text(encoding="utf-8"))
    per = d.get("perimetre") or {}
    fiches = {norm(f.get("nom")) for f in ((d.get("fiches") or {}).get("fiches") or []) if f.get("nature") != "profile"}
    acteurs = len((d.get("acteurs") or {}).get("acteurs") or [])
    return per.get("perimetre"), fiches, acteurs, json.loads((run / "99-rapport.json").read_text(encoding="utf-8"))["verdict"]

# la grille écrite d'avance et le score de gpt : dans les résultats de la répétition de gpt
gpt_rep = json.loads((RUNS / "20261013-082203-repetition-rejouee" / "repetition.json").read_text(encoding="utf-8"))
attendu = {l["brief"]: l.get("perimetre_attendu") for l in gpt_rep}
# les apps fabriquées depuis les lectures Claude : toutes les répétitions « claude » et les lots, la plus récente l'emporte
apps = {}
for rep in sorted(RUNS.glob("*-repetition-*")):
    if not (rep / "repetition.json").exists():
        continue
    for l in json.loads((rep / "repetition.json").read_text(encoding="utf-8")):
        if "claude" in (l.get("comprehension") or ""):
            x = l.get("essai") or l.get("variante") or {}
            apps[l["brief"]] = (x.get("etape"), "variante" if l.get("variante") else "complète", l["comprehension"])

perim_ok, apps_ok, dans, lignes = 0, 0, 0, []
for brief, att in attendu.items():
    nom = brief.removeprefix("appr-")
    cl, gp = complets(f"*-{nom}-claude-comprendre"), [p for p in complets(f"*-{nom}-comprendre") if "-claude-" not in p.name]
    if not cl or not gp:
        lignes.append(f"  {brief:<28} lecture manquante"); continue
    pc, fc, ac, vc = lire(cl[-1]); pg, fg, ag, vg = lire(gp[-1])
    ok_p = att == "limite" or pc == att
    perim_ok += ok_p
    commun = len(fc & fg) / max(len(fc | fg), 1)
    app = apps.get(brief, ("—", "", ""))
    if att != "hors":
        dans += 1
        apps_ok += app[0] == "fabriquée et jugée"
    lignes.append(f"  {brief:<28} périmètre {pc:<5} ({'ok' if ok_p else 'ERREUR, grille : ' + str(att)}) · rôles {ac} vs {ag} gpt · "
                  f"fiches communes {commun:.0%} · app : {app[0] or '—'} {app[1]}")
print("\n".join(lignes))
print(f"\nCritère 1 — périmètre juste : {perim_ok}/{len(attendu)} (exigé ≥ 18/19)")
print(f"Critère 2 — apps jugées bonnes : {apps_ok}/{dans} (exigé ≥ 15/16, score de gpt)")
print("\nVariation (deux lectures Claude du même brief) :")
for nom in ("cabinet-pluri", "autocars", "c2-erp-compta"):
    cl = complets(f"*-{nom}-claude-comprendre")
    if len(cl) >= 2:
        (p1, f1, a1, _), (p2, f2, a2, _) = lire(cl[-2]), lire(cl[-1])
        print(f"  {nom:<16} périmètre {p1}/{p2} · rôles {a1}/{a2} · fiches communes {len(f1 & f2) / max(len(f1 | f2), 1):.0%}")
