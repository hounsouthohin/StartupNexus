"""Coût réel des passages : additionne les jetons enregistrés et les convertit en dollars.
Prix publics relevés le 7 oct 2026 sur des sites tiers (à vérifier sur les pages officielles) :
$ par million de jetons. Les jetons de « réflexion » des modèles qui raisonnent sont comptés en sortie.
Usage : python cout.py"""
import json
from pathlib import Path

PRIX = {  # (entrée, sortie) en $ US par million de jetons
    "gpt-5.4-mini": (0.75, 4.50),
    "gpt-5.5": (5.00, 30.00),
    "gemini-pro-latest": (2.00, 12.00),
}

root = Path(__file__).parent / "sorties"
total = 0.0
for model_dir in sorted(p for p in root.iterdir() if p.is_dir()):
    for run in sorted(p for p in model_dir.iterdir() if p.is_dir() and "-passe" in p.name):
        files = sorted(run.glob("*.json"))
        # compté appel par appel depuis le journal : un brief qui échoue en route a quand même consommé
        calls = [x for f in files for x in json.loads(f.read_text(encoding="utf-8")).get("journal", [])]
        tin = sum(x.get("jetons_entree", 0) for x in calls)
        tout = sum(x.get("jetons_sortie", 0) for x in calls)
        pin, pout = PRIX.get(model_dir.name, (0, 0))
        cost = tin / 1e6 * pin + tout / 1e6 * pout
        total += cost
        per = cost / len(files) if files else 0
        print(f"{model_dir.name:<14} {run.name:<11} briefs={len(files):>2}  jetons={tin:>7}+{tout:>7}  "
              f"coût={cost:5.2f} $  soit {per:.3f} $ par brief")
print(f"\nTotal mesuré (versions 2 et suivantes) : {total:.2f} $ US")
