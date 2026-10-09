"""PREUVE que les tests d'écran attrapent les erreurs (test de mutation, comme l'étude 04 pour le testeur).

On casse volontairement une app fabriquée, UNE erreur à la fois : les tests d'écran doivent échouer.
Puis on remet tout en place (témoin) : ils doivent repasser. Les erreurs sont TIRÉES DE LA MATRICE de
l'app (N1.1b) : la preuve vaut pour n'importe quelle app, pas seulement pour la médiathèque.
À rejouer chaque fois qu'on touche aux pièces d'écran ou aux tests d'écran.

    python -m usine.preuve_ecrans runs/<n°> [e2e/autre.spec.ts …]
"""
from __future__ import annotations

import copy
import json
import os
import subprocess
import sys
from pathlib import Path

from .assembler import _port_libre, _serveur

PEUT_AVANT = "return !!etatActuel && !!d.transitions?.[etatActuel]?.includes(action.slice(5));"


def _ligne(texte: str, debut: str) -> tuple[str, object]:
    """La ligne « export const X… = <json>; » de droits.ts, et sa valeur."""
    ligne = next(l for l in texte.splitlines() if l.startswith(debut))
    return ligne, json.loads(ligne.split(" = ", 1)[1].rstrip(";"))


def _remplace(ligne: str, valeur) -> str:
    return ligne.split(" = ", 1)[0] + " = " + json.dumps(valeur, ensure_ascii=False) + ";"


def mutations(app: Path) -> list[tuple[str, str, str, str]]:
    """(ce qu'on casse, fichier, texte d'origine, texte cassé) — chacune choisie dans la matrice de l'app."""
    droits = (app / "lib" / "droits.ts").read_text(encoding="utf-8")
    notice = (app / "lib" / "notice.ts").read_text(encoding="utf-8")
    l_mat, matrice = _ligne(droits, "export const MATRICE")
    l_menu, menu = _ligne(droits, "export const MENU")
    roles = list(matrice)
    out = []

    def mut(quoi, transforme):
        m = copy.deepcopy(matrice)
        transforme(m)
        out.append((quoi, "lib/droits.ts", l_mat, _remplace(l_mat, m)))

    # 1. un rôle reçoit « créer » sur une fiche qui a un bouton de création, sans en avoir le droit
    a_bouton = sorted({x.split('"', 1)[0] for x in notice.split('"cree": "')[1:]})   # fiches « créées d'un clic »
    for fiche in a_bouton:
        sans = next((r for r in roles if not matrice[r].get(fiche, {}).get("creer")), None)
        if sans:
            mut(f"droits : « {sans} » reçoit « créer » sur {fiche}",
                lambda m, r=sans, f=fiche: m[r].setdefault(f, {}).update(creer=True))
            break
    # 2. un rôle perd une de ses étapes
    for r in roles:
        for fiche, d in matrice[r].items():
            if d.get("transitions"):
                depart = next(s for s, ts in d["transitions"].items() if ts)
                def retire(m, r=r, f=fiche, s=depart):
                    m[r][f]["transitions"][s] = m[r][f]["transitions"][s][:-1]
                    if not m[r][f]["transitions"][s]:
                        del m[r][f]["transitions"][s]
                mut(f"droits : « {r} » perd l'étape « {depart} → {d['transitions'][depart][-1]} » sur {fiche}", retire)
                break
        else:
            continue
        break
    # 3. un rôle gagne une étape qu'il n'a pas, sur une fiche qu'il voit (et qui a un circuit)
    circuits = {f: (r, d["transitions"]) for r in roles for f, d in matrice[r].items() if d.get("transitions")}
    for fiche, (_, tr) in circuits.items():
        r2 = next((r for r in roles if r != "visitor" and matrice[r].get(fiche, {}).get("voir")
                   and not matrice[r][fiche].get("transitions")), None)
        if r2:
            mut(f"droits : « {r2} » gagne les étapes de {fiche}", lambda m, r=r2, f=fiche, t=tr: m[r][f].update(transitions=t))
            break
    # 4. un rôle perd « voir » sur une liste de son menu
    for r in roles:
        f = next((x["fiche"] for x in menu if x["chemin"].startswith("/f/") and matrice[r].get(x["fiche"], {}).get("voir")), None)
        if f:
            mut(f"droits : « {r} » perd « voir » sur {f}", lambda m, r=r, f=f: m[r][f].pop("voir"))
            break
    # 5. une fiche disparaît du menu
    if menu:
        out.append((f"menu : « {menu[-1]['libelle']} » disparaît", "lib/droits.ts", l_menu, _remplace(l_menu, menu[:-1])))
    # 6. une pièce fixe : les boutons de décision ne sont plus filtrés par rôle
    out.append(("pièce fixe : les boutons de décision ne sont plus filtrés par rôle", "lib/peut.ts", PEUT_AVANT, "return true;"))
    return out


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


def main(run: Path, specs: list[str]) -> dict:
    app = run / "app"
    resultats = []
    liste = mutations(app)
    for i, (quoi, fichier, avant, apres) in enumerate(liste, 1):
        chemin = app / fichier
        origine = chemin.read_text(encoding="utf-8")
        if avant not in origine:
            raise SystemExit(f"mutation {i} non appliquable : texte introuvable dans {fichier}")
        print(f"▶ mutation {i}/{len(liste)} : {quoi} …", flush=True)
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
    bilan = {}
    for s in specs:
        attrapees = sum(1 for _, v in resultats if v[s] != "passe")
        bilan[s] = {"attrapees": attrapees, "total": len(liste), "temoin": temoin[s],
                    "detail": [{"sabotage": q, "verdict": v[s]} for q, v in resultats]}
        print(f"\n{s} : {attrapees}/{len(liste)} erreurs attrapées ; témoin : {temoin[s]}")
    (run / "preuve-ecrans.json").write_text(json.dumps(bilan, ensure_ascii=False, indent=2), encoding="utf-8")
    return bilan


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main(Path(sys.argv[1]), sys.argv[2:] or ["e2e/roles.spec.ts"])
