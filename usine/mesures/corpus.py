"""MESURE D'UNE RÉPÉTITION (0 $) : ce que le corpus dit de l'usine, à partir des résultats déjà écrits.

  - périmètre : la réponse du lecteur 5 contre la grille écrite AVANT (« limite » : les deux acceptées) ;
  - fabrication : apps fabriquées et jugées (description complète ou variante), échecs par étape ;
  - blocs manquants : combien de briefs demandent chaque bloc pas encore construit (refus de la description) ;
  - hors stock : combien de briefs du périmètre demandent chaque catégorie (lecteur 5) ;
  - lecteurs : réponses refusées par les contrôles puis redemandées (stabilité) ; champs « nécessaires » ;
  - coût réel.
Écrit `mesure.md` dans le dossier de la (dernière) répétition.

    python -m usine.mesures.corpus runs/<rep1> [runs/<rep2> …]
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
RUNS = RACINE / "runs"


def lignes_de(dossiers: list[Path]) -> list[dict]:
    """Les lignes de plusieurs répétitions ; pour un même brief, la plus récente l'emporte."""
    par_brief: dict[str, dict] = {}
    for d in dossiers:
        for l in json.loads((d / "repetition.json").read_text(encoding="utf-8")):
            par_brief[l["brief"]] = l
    return list(par_brief.values())


def mesurer(dossiers: list[Path]) -> str:
    lignes = lignes_de(dossiers)
    n = len(lignes)
    perim_ok, perim_faux, hors_stock, blocs, etapes, refus_lecteurs, cout = 0, [], Counter(), Counter(), Counter(), Counter(), 0.0
    fabriquees, variantes, dans, champs, necessaires = 0, 0, 0, 0, 0
    for l in lignes:
        cout += l.get("cout", 0)
        run_c = RUNS / l["comprehension"]
        lect = json.loads((run_c / "lecteurs.json").read_text(encoding="utf-8")) if (run_c / "lecteurs.json").exists() else {}
        obtenu = (lect.get("perimetre") or {}).get("perimetre")
        attendu = l.get("perimetre_attendu")
        if attendu == "limite" or obtenu == attendu:
            perim_ok += 1
        else:
            perim_faux.append(f"{l['brief']} : attendu {attendu}, obtenu {obtenu}")
        for x in lect.get("journal", []):
            if x.get("erreurs"):
                refus_lecteurs[x["lecteur"]] += 1
        if obtenu == "dans":
            dans += 1
            for c in {h["categorie"] for h in (lect.get("perimetre") or {}).get("hors_stock", [])}:
                hors_stock[c] += 1
        for b in (l.get("refus") or {}).get("blocs", []):
            blocs[b] += 1
        for f in ((lect.get("champs") or {}).get("fiches") or []):
            champs += len(f.get("champs", []))
            necessaires += sum(1 for c in f.get("champs", []) if c.get("origine") == "necessaire")
        e, v = l.get("essai") or {}, l.get("variante") or {}
        if e.get("etape") == "fabriquée et jugée":
            fabriquees += 1
        elif v.get("etape") == "fabriquée et jugée":
            variantes += 1
        for x in (e, v):
            if x and x.get("etape") not in (None, "fabriquée et jugée"):
                etapes[x["etape"]] += 1

    pct = lambda a, b: f"{a}/{b} ({100 * a / b:.0f} %)" if b else "—"
    out = [f"# Mesure de la répétition — {', '.join(d.name for d in dossiers)}", "",
           f"- Briefs : **{n}** ; dans le périmètre selon le lecteur 5 : {dans}",
           f"- Périmètre juste : **{pct(perim_ok, n)}**" + ("" if not perim_faux else " — faux : " + " ; ".join(perim_faux)),
           f"- Apps fabriquées et jugées : **{fabriquees}** complètes + **{variantes}** variantes (sur {dans} du périmètre)",
           f"- Coût réel des compréhensions : **{cout:.2f} $** ({cout / max(n, 1):.3f} $ par brief en moyenne)",
           f"- Champs lus par l'IA : {champs}, dont {pct(necessaires, champs)} « nécessaires » (le brief n'en disait rien)", "",
           "## Blocs pas encore construits (briefs qui les demandent)", ""]
    out += [f"- {b} : {c}/{dans}" for b, c in blocs.most_common()] or ["- aucun"]
    out += ["", "## Hors stock demandé (briefs du périmètre)", ""]
    out += [f"- {c} : {k}/{dans}" for c, k in hors_stock.most_common()] or ["- aucun"]
    out += ["", "## Échecs de fabrication (par étape)", ""]
    out += [f"- {s} : {k}" for s, k in etapes.most_common()] or ["- aucun"]
    out += ["", "## Réponses des lecteurs refusées par les contrôles (puis redemandées)", ""]
    out += [f"- {lect} : {k}" for lect, k in refus_lecteurs.most_common()] or ["- aucune"]
    return "\n".join(out) + "\n"


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    dossiers = [Path(a) for a in sys.argv[1:]]
    texte = mesurer(dossiers)
    (dossiers[-1] / "mesure.md").write_text(texte, encoding="utf-8")
    print(texte)
    return 0


if __name__ == "__main__":
    sys.exit(main())
