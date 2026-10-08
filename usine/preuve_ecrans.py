"""PREUVE que les tests d'écran attrapent les erreurs (test de mutation, comme l'étude 04 pour le testeur).

On casse volontairement une app fabriquée depuis l'exemple médiathèque, UNE erreur à la fois : les tests
d'écran doivent échouer. Puis on remet tout en place (témoin) : ils doivent repasser. À rejouer chaque
fois qu'on touche aux pièces d'écran ou aux tests d'écran.

    python -m usine.preuve_ecrans runs/<n°>-mediatheque [e2e/autre.spec.ts …]
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from .assembler import _port_libre, _serveur

# (ce qu'on casse, fichier de l'app, texte d'origine, texte cassé)
MUTATIONS = [
    ("traduction des droits : le visiteur reçoit « créer un emprunt »", "lib/droits.ts",
     '{"visitor": {"Book": {"voir": true}}', '{"visitor": {"Book": {"voir": true}, "Borrowing": {"creer": true}}'),
    ("traduction des droits : le bibliothécaire perd « refuser »", "lib/droits.ts",
     '"requested": ["accepted", "refused"]', '"requested": ["accepted"]'),
    ("traduction du menu : les emprunts disparaissent du menu", "lib/droits.ts",
     ', {"fiche": "Borrowing", "chemin": "/f/Borrowing", "libelle": "Emprunts", "action": "voir"}', ""),
    ("pièce fixe : les boutons de décision ne sont plus filtrés par rôle", "lib/peut.ts",
     "return !!etatActuel && !!d.transitions?.[etatActuel]?.includes(action.slice(5));", "return true;"),
]


def _run(cmd: str, app: Path, env: dict | None = None) -> tuple[int, str]:
    r = subprocess.run(cmd, cwd=app, shell=True, capture_output=True, text=True, encoding="utf-8",
                       errors="replace", env={**os.environ, **(env or {})})
    return r.returncode, r.stdout + r.stderr


def _jouer(app: Path, specs: list[str], log: Path) -> dict[str, str]:
    """Construit l'app telle qu'elle est, la démarre, joue chaque fichier de tests ; renvoie un verdict par fichier.
    Le détail de chaque passage est gardé à côté du journal du serveur (<log>-<fichier de tests>.log)."""
    code, sortie = _run("npx next build", app, {"NEXT_TELEMETRY_DISABLED": "1"})
    if code:
        return {s: "l'app ne se construit plus (erreur attrapée avant les tests)" for s in specs}
    verdicts = {}
    port = _port_libre()
    with _serveur(app, port, log):
        for spec in specs:
            code, sortie = _run("npx tsx --env-file=.env.local scripts/seed.ts", app)
            if code:
                raise RuntimeError(f"données de départ non rechargées :\n{sortie[-800:]}")
            code, sortie = _run(f"npx playwright test {spec}", app, {"BASE_URL": f"http://localhost:{port}"})
            log.with_name(f"{log.stem}-{Path(spec).stem}.log").write_text(sortie, encoding="utf-8")
            echecs = sorted({l.split("›", 1)[1].split(" (")[0].strip(" ─") for l in sortie.splitlines()
                             if "›" in l and not l.strip().startswith(("ok", "-"))})
            verdicts[spec] = ("ÉCHOUE — " + " | ".join(echecs)) if code else "passe"
    return verdicts


def main(run: Path, specs: list[str]) -> None:
    app = run / "app"
    resultats = []
    for i, (quoi, fichier, avant, apres) in enumerate(MUTATIONS, 1):
        chemin = app / fichier
        origine = chemin.read_text(encoding="utf-8")
        if avant not in origine:
            raise SystemExit(f"mutation {i} non appliquable : texte introuvable dans {fichier}")
        print(f"▶ mutation {i}/{len(MUTATIONS)} : {quoi} …", flush=True)
        try:
            chemin.write_text(origine.replace(avant, apres, 1), encoding="utf-8")
            v = _jouer(app, specs, run / "logs" / f"preuve-mutation-{i}.log")
        finally:
            chemin.write_text(origine, encoding="utf-8")
        for s, verdict in v.items():
            print(f"    {s} : {verdict}", flush=True)
        resultats.append((quoi, v))
    print("▶ témoin : l'app d'origine, rien de cassé …", flush=True)
    temoin = _jouer(app, specs, run / "logs" / "preuve-temoin.log")
    for s, verdict in temoin.items():
        print(f"    {s} : {verdict}", flush=True)
    for s in specs:
        attrapees = sum(1 for _, v in resultats if v[s] != "passe")
        print(f"\n{s} : {attrapees}/{len(MUTATIONS)} erreurs attrapées ; témoin : {temoin[s]}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main(Path(sys.argv[1]), sys.argv[2:] or ["e2e/roles.spec.ts"])
