"""La commande de l'usine.

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
    f = sub.add_parser("fabriquer", help="description → app qui tourne")
    f.add_argument("description", type=Path)
    d = sub.add_parser("demarrer", help="lancer une app fabriquée")
    d.add_argument("run", type=Path)
    d.add_argument("--port", type=int, default=3300)
    args = p.parse_args()
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
