"""PREUVE du contrôle des failles connues (registre n° 60, conception/0b-nextjs.md).

Trois cas, sur des copies du fichier de verrouillage du squelette (rien n'est installé) :
  1. SABOTAGE : le fichier d'avant la montée de version (commit 8d4e288e, Next.js 16.4.0, 2 failles critiques)
     doit être REFUSÉ, avec « next » parmi les paquets critiques ;
  2. TÉMOIN : le squelette actuel doit être ACCEPTÉ (0 critique) ;
  3. SANS RÉSEAU : registre injoignable → l'audit doit être « non fait », jamais « accepté ».

    python -m usine.preuve_audit
"""
from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from .assembler import RACINE, SQUELETTE, auditer, resume_audit

AVANT = "8d4e288e"     # dernier commit avant la montée de version
FICHIERS = ("package.json", "package-lock.json")


def _copie_git(dossier: Path) -> None:
    for f in FICHIERS:
        contenu = subprocess.run(["git", "show", f"{AVANT}:usine/modele-app/{f}"], cwd=RACINE, capture_output=True,
                                 check=True).stdout
        (dossier / f).write_bytes(contenu)


def _copie_squelette(dossier: Path) -> None:
    for f in FICHIERS:
        shutil.copyfile(SQUELETTE / f, dossier / f)


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    cas = [
        ("sabotage : le verrouillage d'avant (Next.js 16.4.0)", _copie_git, None,
         lambda a: a["fait"] and a["critical"] > 0 and "next" in a["paquets_critiques"], "refusé, avec next"),
        ("témoin : le squelette actuel", _copie_squelette, None,
         lambda a: a["fait"] and a["critical"] == 0, "accepté (0 critique)"),
        ("sans réseau : registre injoignable", _copie_squelette, {"npm_config_registry": "http://127.0.0.1:9/"},
         lambda a: not a["fait"], "non fait"),
    ]
    reussis = 0
    with tempfile.TemporaryDirectory(prefix="preuve-audit-") as tmp:
        for i, (nom, preparer, env, attendu, texte) in enumerate(cas, 1):
            d = Path(tmp) / str(i)
            d.mkdir()
            preparer(d)
            a = auditer(d, d / "audit.log", env=env)
            ok = attendu(a)
            reussis += ok
            print(f"{'✓' if ok else '✗'} {nom} — attendu : {texte} — obtenu : {resume_audit(a)}"
                  + (f" ; critiques : {', '.join(a['paquets_critiques'])}" if a.get("paquets_critiques") else ""))
    print(f"\n{reussis}/{len(cas)} cas conformes")
    return 0 if reussis == len(cas) else 1


if __name__ == "__main__":
    sys.exit(main())
