"""La CARTE DES BLOCS : une page HTML (runs/carte-des-blocs.html) qui montre chaque bloc de l'usine,
ses 4 parties (construire, écran, juger, prouver), et les scores des dernières preuves par sabotage.

    python -m usine carte [--sans-ouvrir]
"""
from __future__ import annotations

import html
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from . import BLOCS, RACINE, SANS_ECRAN, Bloc, controle

SORTIE = RACINE / "runs" / "carte-des-blocs.html"


def bloc_du_sabotage(m: dict) -> str:
    """À quel bloc appartient la règle qu'un sabotage abîme (preuve-regles.json)."""
    r, d = m["regle"], m["description"]
    if "createdAt != before().createdAt" in r:
        return "garantie:date"
    if r.startswith("@@deny('post-update'"):
        return "garantie:proprietaire"
    if m["operateur"] == "oublier une condition":
        cond = d.split("«", 1)[1].split("»", 1)[0] if "«" in d else d
        if "check(" in cond:
            return "garantie:cloture"
        if "== before()." in cond and "status" not in cond:
            return "garantie:etape-seule"
    if "'read'" in r:
        return "portee:via" if "?[true]" in r else "action:see"
    if "'create'" in r:
        return "action:create"
    if "'post-update'" in r:
        return "action:transition" if "before().status" in r else "action:edit"
    if "'update'" in r:
        return "action:edit"
    if "'delete'" in r:
        return "action:delete"
    return "?"


def bloc_du_sabotage_ecran(s: str) -> str:
    if "créer" in s:
        return "action:create"
    if "étape" in s or "décision" in s:
        return "action:transition"
    return "action:see"   # « perd voir », « menu »


def preuves() -> tuple[dict, list[str]]:
    """Scores par bloc, tirés des DERNIÈRES preuves de chaque app (fichiers écrits par les outils de preuve)."""
    par_bloc: dict = defaultdict(lambda: {"tues": 0, "total": 0, "ecrans": [0, 0]})
    sources = []
    for f in sorted(RACINE.glob("runs/*/preuve-regles.json")):
        for m in json.loads(f.read_text(encoding="utf-8")):
            if m["verdict"] == "invalide":
                continue
            b = par_bloc[bloc_du_sabotage(m)]
            b["total"] += 1
            b["tues"] += m["verdict"] == "tué"
        sources.append(f"règles : {f.parent.name}")
    for f in sorted(RACINE.glob("runs/*/preuve-ecrans.json")):
        for spec, r in json.loads(f.read_text(encoding="utf-8")).items():
            for x in r["detail"]:
                e = par_bloc[bloc_du_sabotage_ecran(x["sabotage"])]["ecrans"]
                e[1] += 1
                e[0] += x["verdict"] != "passe"
        sources.append(f"écrans : {f.parent.name}")
    return par_bloc, sources


def _partie(b: Bloc, nom: str) -> str:
    p = b.parties[nom]
    if p:
        return (f'<li class="ok" title="{html.escape(p.fichier)} — {html.escape(p.note)}"><b>✔</b> {nom}'
                f'<small>{html.escape(p.note or Path(p.fichier).name)}</small></li>')
    if nom == "écran" and b.id in SANS_ECRAN:
        return f'<li class="na"><b>—</b> {nom}<small>sans objet (règle serveur)</small></li>'
    return f'<li class="no"><b>○</b> {nom}<small>à faire</small></li>'


def page() -> str:
    erreurs = controle()
    scores, sources = preuves()
    familles: dict[str, list[Bloc]] = defaultdict(list)
    for b in BLOCS:
        familles[b.famille].append(b)
    compte = {e: sum(1 for b in BLOCS if b.etat == e) for e in ("complet", "partiel", "refusé")}
    cartes = []
    for fam, blocs in familles.items():
        items = []
        for b in blocs:
            s = scores.get(b.id)
            preuve = ""
            if s and s["total"]:
                preuve += f'<p class="score">sabotages des règles : <b>{s["tues"]}/{s["total"]}</b> attrapés</p>'
            if s and s["ecrans"][1]:
                preuve += f'<p class="score">sabotages des écrans : <b>{s["ecrans"][0]}/{s["ecrans"][1]}</b> attrapés</p>'
            if b.refuse:
                corps = (f'<p class="refus">⛔ pas encore construit — refusé franchement par l\'usine '
                         f'({html.escape(Path(b.refuse.fichier).name)})</p>')
            else:
                corps = "<ul>" + "".join(_partie(b, n) for n in ("construire", "écran", "juger", "prouver")) + "</ul>"
            notes = "".join(f"<li>{html.escape(n)}</li>" for n in b.notes)
            items.append(f'<article class="bloc {b.etat}"><header><h3>{html.escape(b.nom)}</h3>'
                         f'<span class="etat">{b.etat}</span></header><p class="role">{html.escape(b.role)}</p>'
                         f'{corps}{preuve}{"<ul class=notes>" + notes + "</ul>" if notes else ""}</article>')
        cartes.append(f'<section><h2>{html.escape(fam)}</h2><div class="grille">{"".join(items)}</div></section>')
    verdict = ('<p class="controle ok">✔ Contrôle d\'architecture : chaque mot du vocabulaire a son bloc, '
               'chaque partie déclarée existe.</p>' if not erreurs else
               '<p class="controle ko">✗ Contrôle d\'architecture : ' + "<br>".join(html.escape(e) for e in erreurs) + "</p>")
    return f"""<!doctype html><html lang="fr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>Carte des blocs</title>
<style>
:root {{ --fond:#f6f7f9; --carte:#fff; --texte:#1c2330; --doux:#5b6475; --bord:#d9dde5;
  --ok:#1f7a4d; --ok-fond:#e6f4ec; --no:#9a6400; --no-fond:#fbf1dc; --ko:#b42318; --ko-fond:#fdecea; --na:#7a8193; }}
@media (prefers-color-scheme: dark) {{ :root {{ --fond:#12161d; --carte:#1b212b; --texte:#e7eaf0; --doux:#a3abbb;
  --bord:#2c3442; --ok:#5fd29a; --ok-fond:#163527; --no:#f0b94f; --no-fond:#3a2d12; --ko:#ff8a80; --ko-fond:#3d1b18; --na:#8a92a3; }} }}
* {{ box-sizing:border-box }} body {{ margin:0; background:var(--fond); color:var(--texte);
  font:15px/1.45 system-ui, -apple-system, "Segoe UI", sans-serif; }}
main {{ max-width:1180px; margin:0 auto; padding:24px 16px 48px }}
h1 {{ font-size:26px; margin:0 0 4px }} .sous {{ color:var(--doux); margin:0 0 16px }}
.resume {{ display:flex; gap:10px; flex-wrap:wrap; margin:12px 0 }}
.resume span {{ background:var(--carte); border:1px solid var(--bord); border-radius:8px; padding:6px 12px }}
.legende {{ color:var(--doux); font-size:13px }}
.controle {{ border-radius:8px; padding:10px 14px; margin:14px 0 }} .controle.ok {{ background:var(--ok-fond); color:var(--ok) }}
.controle.ko {{ background:var(--ko-fond); color:var(--ko) }}
h2 {{ font-size:18px; margin:28px 0 10px; padding-bottom:6px; border-bottom:1px solid var(--bord) }}
.grille {{ display:grid; grid-template-columns:repeat(auto-fill, minmax(260px, 1fr)); gap:12px }}
.bloc {{ background:var(--carte); border:1px solid var(--bord); border-radius:10px; padding:12px 14px }}
.bloc header {{ display:flex; justify-content:space-between; align-items:baseline; gap:8px }}
.bloc h3 {{ font-size:16px; margin:0 }} .etat {{ font-size:12px; border-radius:20px; padding:1px 9px }}
.complet .etat {{ background:var(--ok-fond); color:var(--ok) }} .partiel .etat {{ background:var(--no-fond); color:var(--no) }}
.refusé .etat {{ background:var(--ko-fond); color:var(--ko) }}
.role {{ color:var(--doux); font-size:13px; margin:6px 0 8px }}
.bloc ul {{ list-style:none; padding:0; margin:0; display:grid; grid-template-columns:repeat(2, minmax(0, 1fr)); gap:6px }}
.bloc li {{ border-radius:6px; padding:5px 8px; font-size:13px; min-width:0 }}
.bloc li small {{ display:block; font-size:11px; opacity:.85; overflow-wrap:anywhere }}
li.ok {{ background:var(--ok-fond); color:var(--ok) }} li.no {{ background:var(--no-fond); color:var(--no) }}
li.na {{ border:1px dashed var(--bord); color:var(--na) }}
.refus {{ background:var(--ko-fond); color:var(--ko); border-radius:6px; padding:8px; font-size:13px; margin:0 }}
.score {{ margin:8px 0 0; font-size:13px }}
ul.notes {{ display:block; margin-top:8px; color:var(--doux) }} ul.notes li {{ padding:2px 0; font-size:12px }}
ul.notes li::before {{ content:"• " }}
footer {{ margin-top:28px; color:var(--doux); font-size:12px }}
</style></head><body><main>
<h1>Carte des blocs de l'usine</h1>
<p class="sous">Chaque mot que l'usine sait exprimer, et ses 4 parties : <b>construire</b> (règles, base) ·
<b>écran</b> · <b>juger</b> (testeur, tests d'écran) · <b>prouver</b> (fabriqué dans une app, juges prouvés par sabotage).</p>
<div class="resume"><span>✔ {compte['complet']} complets</span><span>◐ {compte['partiel']} partiels</span>
<span>⛔ {compte['refusé']} refusés (pas encore construits)</span><span>{len(BLOCS)} blocs</span></div>
<p class="legende">✔ la partie existe · ○ à faire · — sans objet · ⛔ l'usine refuse ce mot franchement plutôt que de le faire à moitié.
Les sabotages qui survivent sont presque tous sans effet (règles en double) ou de la famille bénigne connue ; leur analyse est dans USINE.md.</p>
{verdict}
{"".join(cartes)}
<footer>Généré le {datetime.now():%d/%m/%Y à %H:%M} par <code>python -m usine carte</code> ·
preuves lues : {html.escape(" · ".join(sources) or "aucune")}</footer>
</main></body></html>"""


def generer(ouvrir: bool = True) -> tuple[Path, list[str]]:
    SORTIE.parent.mkdir(exist_ok=True)
    SORTIE.write_text(page(), encoding="utf-8")
    if ouvrir:
        import os
        os.startfile(SORTIE)  # noqa: S606 — ouvre la page dans le navigateur (Windows)
    return SORTIE, controle()
