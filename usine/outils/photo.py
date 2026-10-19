"""PHOTO de tout ce que l'usine produit (sans rien fabriquer) : matrice + traductions, pour chaque app d'une répétition
et les 3 exemples. Sert à prouver qu'une restructuration ne change aucun résultat : photo avant, photo après, comparer.py.
Usage : python usine/outils/photo.py <dossier de sortie> [<répétition de référence>]"""
import json, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
R = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(R))
from usine.description import Description
from usine.matrice import compute_matrix
from usine.traduire.schema import traduire_schema
from usine.traduire.ecran import traduire_droits, traduire_notice, traduire_roles
from usine.traduire.depart import traduire_depart
from usine.repetition import derniere_comprehension, accepter_propositions, variante, refus

sortie = Path(sys.argv[1]); sortie.mkdir(parents=True, exist_ok=True)
rep = sys.argv[2] if len(sys.argv) > 2 else "20261013-082203-repetition-rejouee"
sources = [(ex, json.loads((R / "usine" / "exemples" / f"{ex}.json").read_text(encoding="utf-8"))) for ex in ("types", "mediatheque", "union-sportive")]
for l in json.loads((R / "runs" / rep / "repetition.json").read_text(encoding="utf-8")):
    run_c = derniere_comprehension(l)
    src = next((run_c / f for f in ("description.json", "description-brute.json") if (run_c / f).exists()), None)
    if src:
        b = json.loads(src.read_text(encoding="utf-8")); accepter_propositions(b, run_c); sources.append((l["brief"], b))
for nom, brut in sources:
    retire = []
    for _ in range(3):
        r = refus(brut)
        if not r:
            break
        d2, ret = variante(brut["acces"], r)
        if not ret:
            break
        retire += ret
        g = {e["name"] for e in d2["entities"]}
        brut = {**brut, "acces": d2, "champs": {k: v for k, v in brut["champs"].items() if k in g}, "ecran": {k: v for k, v in brut["ecran"].items() if k in g}}
    d = sortie / nom; d.mkdir(exist_ok=True)
    (d / "variante.txt").write_text("\n".join(retire) + ("\nREFUS RESTANT : " + refus(brut) if refus(brut) else ""), encoding="utf-8")
    if refus(brut):
        continue
    desc = Description.model_validate(brut); m = compute_matrix(desc.acces)
    (d / "matrice.json").write_text(m.model_dump_json(indent=1), encoding="utf-8")
    (d / "schema.zmodel").write_text(traduire_schema(desc, m), encoding="utf-8")
    (d / "notice.ts").write_text(traduire_notice(desc, m), encoding="utf-8")
    (d / "droits.ts").write_text(traduire_droits(desc, m), encoding="utf-8")
    (d / "roles.ts").write_text(traduire_roles(desc), encoding="utf-8")
    (d / "depart.json").write_text(json.dumps(traduire_depart(desc, m), ensure_ascii=False, indent=1), encoding="utf-8")
print(f"{len(sources)} apps photographiées dans {sortie}")
