"""DONNÉES DU TABLEAU DE BORD (0 $) : les chiffres de la page « Usine d'assemblage », lus dans les sources de
l'usine — jamais recopiés à la main. Écrit runs/tableau/*.json (une source par fichier), que la page affiche.

  apps.json        une ligne par brief de la dernière répétition : app complète / variante / hors périmètre, juges
  convergence.json la table « Convergence » d'USINE.md §7 (défauts nouveaux par app nouvelle)
  registre.json    le registre des corrections d'USINE.md §7 (n°, date, correction, nature)
  natures.json     le registre compté par nature (défaut de l'usine, trou du juge, mon erreur…)
  blocs.json       le catalogue des blocs (usine/blocs) : famille, nom, état
  besoins.json     ce que les vrais briefs demandent (mesure du corpus) : blocs manquants et hors stock

    python -m usine.tableau runs/<n°>-repetition-… [runs/<n°>-repetition-… …]
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

from .blocs import BLOCS

RACINE = Path(__file__).resolve().parents[1]
RUNS = RACINE / "runs"
SORTIE = RUNS / "tableau"


def _lignes_table(texte: str, apres: str) -> list[list[str]]:
    """Les lignes de la première table markdown qui suit le repère `apres` (cellules nettoyées)."""
    debut = texte.index(apres)
    lignes, dedans = [], False
    for l in texte[debut:].splitlines():
        if l.startswith("|"):
            dedans = True
            cellules = [c.strip() for c in l.strip().strip("|").split("|")]
            if not set("".join(cellules)) <= set("-: "):
                lignes.append(cellules)
        elif dedans:
            break
    return lignes[1:]          # sans l'en-tête


def _nature(texte: str) -> str:
    """La nature PRINCIPALE : celle que la colonne cite en premier (« défaut de l'usine + erreur du banc »)."""
    t = texte.lower()
    cles = (("mon erreur", "Mon erreur"), ("trou", "Trou d'un juge"), ("outillage", "Outillage"),
            ("documentation", "Documentation"), ("erreur du banc", "Erreur du banc"), ("défaut", "Défaut de l'usine"))
    trouvees = sorted((t.index(c), nom) for c, nom in cles if c in t)
    return trouvees[0][1] if trouvees else "Autre"


def apps(rep: Path) -> list[dict]:
    out = []
    for l in json.loads((rep / "repetition.json").read_text(encoding="utf-8")):
        e = l.get("essai") or {}
        v = l.get("variante") or {}
        x = e or v
        regles = re.match(r"(\d+)/(\d+)", x.get("regles", "") or "")
        ecrans = re.match(r"(\d+) passed", x.get("ecrans", "") or "")
        statut = ("hors périmètre" if "HORS" in l.get("verdict_comprehension", "") else
                  "complète" if e.get("etape") == "fabriquée et jugée" else
                  "variante" if v.get("etape") == "fabriquée et jugée" else "échec")
        out.append({"brief": l["brief"], "lot": "apprentissage" if l["brief"].startswith("appr-") else "corpus 2",
                    "statut": statut, "retire": "; ".join(v.get("sans", [])),
                    "regles_ok": int(regles[1]) if regles else None, "regles": int(regles[2]) if regles else None,
                    "ecrans_ok": int(ecrans[1]) if ecrans else None,
                    "champs_proposes": l.get("client_simule") or 0, "cout": round(l.get("cout", 0), 3)})
    return out


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    # (16 oct) plusieurs répétitions (le corpus lu par lots) : une ligne par brief, la plus récente l'emporte ;
    # la mesure est lue dans la dernière (python -m usine.mesures.corpus l'y écrit)
    reps = [Path(a) for a in sys.argv[1:]]
    rep = reps[-1]
    usine = (RACINE / "USINE.md").read_text(encoding="utf-8")
    SORTIE.mkdir(parents=True, exist_ok=True)
    registre = [{"n": int(c[0]), "date": c[1], "correction": re.sub(r"\*\*", "", c[2]), "nature": _nature(c[3]),
                 "trouvee_par": re.sub(r"\*\*", "", c[4])}
                for c in _lignes_table(usine, "### Registre des corrections") if c and c[0].isdigit()]
    convergence = [{"moment": re.sub(r"\*\*|\(.*?\)", "", c[0]).strip(), "apps": c[1], "defauts": c[2],
                    "par_app": float(c[3].replace(",", ".")) if re.match(r"^[\d,.]+$", c[3]) else None}
                   for c in _lignes_table(usine, "**Convergence**")]
    natures = [{"nature": k, "corrections": v} for k, v in Counter(r["nature"] for r in registre).most_common()]
    blocs = [{"id": b.id, "famille": b.famille, "nom": b.nom, "etat": b.etat, "role": b.role} for b in BLOCS]
    mesure = (rep / "mesure.md").read_text(encoding="utf-8") if (rep / "mesure.md").exists() else ""
    besoins = []
    for titre, genre in (("## Blocs pas encore construits", "bloc à construire"), ("## Hors stock demandé", "hors stock")):
        if titre in mesure:
            bloc = mesure.split(titre, 1)[1].split("\n## ", 1)[0]
            for m in re.finditer(r"^- (.+?) : (\d+)/(\d+)$", bloc, re.M):
                besoins.append({"besoin": m[1], "genre": genre, "briefs": int(m[2]), "sur": int(m[3])})
    lignes_apps = list({a["brief"]: a for r in reps for a in apps(r)}.values())
    donnees = {"apps": lignes_apps, "convergence": convergence, "registre": registre, "natures": natures,
               "blocs": blocs, "besoins": besoins}
    for nom, lignes in donnees.items():
        (SORTIE / f"{nom}.json").write_text(json.dumps(lignes, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"{nom:<12} {len(lignes):>3} lignes")
    (SORTIE / "source.txt").write_text(f"{', '.join(r.name for r in reps)} · {datetime.now().isoformat(timespec='seconds')}\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
