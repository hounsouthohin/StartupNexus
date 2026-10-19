"""ESSAI A (18 oct) : un critique IA relit le brief et le miroir des lectures du corpus (Opus, 13-16 oct) et
signale ce que l'usine a pu mal comprendre. Par la session Claude isolée (boîte aux lettres, 0 $).
Reprend là où il s'est arrêté (un brief déjà critiqué n'est pas redemandé).

CRITÈRES ÉCRITS AVANT DE LANCER (fiche validée le 18 oct) — adopté seulement si TOUS tiennent :
  1. le paramédical est signalé « cœur non construit », bloquant (obligatoire) ;
  2. les briefs « limite » de la grille (erp-compta, plateforme-educative, restaurant-caisse) : au moins 2/3
     signalés au moins en « important » ;
  3. au moins 70 % des signalements bloquants ou importants sont justes (classés à la main, règle écrite :
     la citation exprime bien un besoin absent du miroir ou contredit par lui ; 10 vérifiés par l'utilisateur) ;
  4. 3 signalements au plus par brief en moyenne.

    python usine/outils/essai_critique.py            (puis ouvrir la session isolée)
    python usine/outils/essai_critique.py --bilan    (critères 1, 2, 4 calculés ; à classer pour le 3)
"""
import json
import sys
from pathlib import Path

import yaml

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE))
from usine.comprendre.critique import Q_CRITIQUE, SortieCritique, controle_critique  # noqa: E402
from usine.comprendre.ia import Budget, client_pour, demander, fin_de_lot  # noqa: E402
from usine.miroir import depuis_run, en_markdown  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
RUNS, SORTIE = RACINE / "runs", RACINE / "runs" / "essai-critique"
LIMITES = ["c2-erp-compta", "c2-plateforme-educative", "c2-restaurant-caisse"]


def lectures() -> dict[str, Path]:
    """La dernière lecture d'Opus de chaque brief du corpus (les essais Sonnet du 15 oct, 09 h, exclus)."""
    noms = [b["project_name"] for b in json.loads((RACINE / "usine/corpus/briefs.json").read_text(encoding="utf-8"))]
    out = {}
    for n in noms:
        rs = sorted(p for p in RUNS.glob(f"*-{n}-claude-comprendre") if (p / "lecteurs.json").exists()
                    and (p / "description-brute.json").exists() and not p.name.startswith("20261015-09"))
        if rs:
            out[n] = rs[-1]
    return out


def lancer() -> None:
    SORTIE.mkdir(parents=True, exist_ok=True)
    client = client_pour("boite")
    for nom, run in lectures().items():
        f = SORTIE / f"{nom}.json"
        if f.exists():
            continue
        brief = (run / "brief.txt").read_text(encoding="utf-8")
        miroir = en_markdown(depuis_run(run)).split("\n---\n")[0]      # la vue du client, sans le volet concepteur
        appels: list = []
        print(f"▶ {nom}", flush=True)
        r = demander(client, Budget("boite", 2.0), Q_CRITIQUE, {"brief": brief, "miroir": miroir},
                     SortieCritique, controle_critique, {"brief": brief}, appels)
        f.write_text(json.dumps({"lecture": run.name, "critique": r.model_dump() if r else None,
                                 "refus": sum(1 for a in appels if a["erreurs"])}, ensure_ascii=False, indent=1), encoding="utf-8")
    fin_de_lot()
    print("FIN — python usine/outils/essai_critique.py --bilan")


def bilan() -> None:
    ref = yaml.safe_load((RACINE / "usine/corpus/references.yaml").read_text(encoding="utf-8"))
    ref = ref if "c2-paramedical-analyse" in ref else next(v for v in ref.values() if isinstance(v, dict) and "c2-paramedical-analyse" in v)
    res = {f.stem: json.loads(f.read_text(encoding="utf-8")) for f in sorted(SORTIE.glob("c2-*.json"))}
    sig = {n: (r["critique"] or {}).get("signalements", []) for n, r in res.items()}
    fort = lambda s: s["gravite"] in ("bloquant", "important")
    c1 = any(s["sorte"] == "coeur_non_construit" and s["gravite"] == "bloquant" for s in sig.get("c2-paramedical-analyse", []))
    c2 = sum(1 for n in LIMITES if any(fort(s) for s in sig.get(n, [])))
    moy = sum(len(v) for v in sig.values()) / max(len(sig), 1)
    print(f"briefs critiqués : {len(res)} (sans réponse acceptée : {sum(1 for r in res.values() if not r['critique'])})")
    print(f"1. paramédical signalé cœur non construit (bloquant) : {'OUI' if c1 else 'NON'}")
    print(f"2. briefs limite signalés au moins « important » : {c2}/3 (exigé : 2)")
    print(f"4. signalements par brief : {moy:.1f} en moyenne (exigé : ≤ 3)")
    lignes = ["| # | Brief | Périmètre attendu | Sorte | Gravité | Explication | Citation | Juste ? |", "|---|---|---|---|---|---|---|---|"]
    k = 0
    for n, ss in sig.items():
        for s in ss:
            if fort(s):
                k += 1
                lignes.append(f"| {k} | {n} | {(ref.get(n) or {}).get('perimetre', '?')} | {s['sorte']} | {s['gravite']} | "
                              f"{s['explication'].replace('|', '/')} | « {s['citation'].replace('|', '/')} » |  |")
    (SORTIE / "a-classer.md").write_text("\n".join(lignes) + "\n", encoding="utf-8")
    print(f"3. à classer à la main : {k} signalements bloquants ou importants → {SORTIE / 'a-classer.md'}")


if __name__ == "__main__":
    bilan() if "--bilan" in sys.argv else lancer()
