"""La commande de l'usine.

    python -m usine comprendre <brief.txt | briefs.json#projet> --nom <nom> [--modele gpt-5.5] [--plafond 0.20]
    python -m usine carte [--sans-ouvrir]
    python -m usine fabriquer usine/exemples/mediatheque.json
    python -m usine demarrer runs/<n°> [--port 3300]
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(prog="usine")
    sub = p.add_subparsers(dest="commande", required=True)
    c = sub.add_parser("comprendre", help="brief → description de l'app (lecteurs IA)")
    c.add_argument("brief")
    c.add_argument("--nom", required=True, help="identifiant court de l'app (minuscules, chiffres, tirets)")
    c.add_argument("--modele", default="gpt-5.5")
    c.add_argument("--plafond", type=float, default=0.20, help="dépense maximale de ce lancement, en $ US")
    c.add_argument("--reprendre", type=Path, help="dossier …-comprendre précédent : ses réponses encore valides sont réutilisées")
    k = sub.add_parser("carte", help="la carte des blocs de l'usine (contrôle d'architecture + page visuelle)")
    k.add_argument("--sans-ouvrir", action="store_true")
    f = sub.add_parser("fabriquer", help="description → app qui tourne")
    f.add_argument("description", type=Path)
    d = sub.add_parser("demarrer", help="lancer une app fabriquée")
    d.add_argument("run", type=Path)
    d.add_argument("--port", type=int, default=3300)
    args = p.parse_args()
    if args.commande == "carte":
        from .blocs.carte import generer
        chemin, erreurs = generer(not args.sans_ouvrir)
        print(f"Carte des blocs : {chemin}")
        print("Contrôle d'architecture : " + ("OK" if not erreurs else "\n- " + "\n- ".join(erreurs)))
        return 1 if erreurs else 0
    if args.commande == "comprendre":
        from .comprendre import comprendre
        comprendre(args.brief, args.nom, args.modele, args.plafond, args.reprendre)
        return 0
    if args.commande == "fabriquer":
        from .assembler import fabriquer
        try:
            fabriquer(args.description)
        except Exception:
            print("\nFabrication interrompue (voir le journal ci-dessus et runs/<n°>/logs/).")
            return 1
        return 0
    app = args.run / "app"
    print(f"App : http://localhost:{args.port}  (Ctrl+C pour arrêter)")
    return subprocess.call(f"npx next start -p {args.port}", cwd=app, shell=True)


if __name__ == "__main__":
    sys.exit(main())
