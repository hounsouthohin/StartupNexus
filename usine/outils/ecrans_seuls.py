"""Rejoue les tests d'écran (copie du squelette) sur une app déjà construite : python ecrans_seuls.py <run>"""
import os
import shutil
import subprocess
import sys
from pathlib import Path

RACINE = Path(r"C:\Users\BAMBARA Arthur\Desktop\StartupNexus")
sys.path.insert(0, str(RACINE))
from usine.assembler import _port_libre, _serveur, dependances  # noqa: E402

run = Path(sys.argv[1])
app = run / "app"
dependances(app, run / "logs" / "installer-ecrans-seuls.log")
shutil.copytree(RACINE / "usine" / "modele-app" / "e2e", app / "e2e", dirs_exist_ok=True)   # noyau + blocs + roles.spec
r = lambda cmd, env=None: subprocess.run(cmd, cwd=app, shell=True, capture_output=True, text=True, encoding="utf-8",
                                          errors="replace", env={**os.environ, **(env or {})})
print(r("npx tsx --env-file=.env.local scripts/seed.ts").stdout.strip())
port = _port_libre()
with _serveur(app, port, run / "logs" / "serveur-ecrans-seuls.log"):
    t = r("npx playwright test", {"BASE_URL": f"http://localhost:{port}"})
print("\n".join(l for l in t.stdout.splitlines() if "›" in l or "passed" in l or "failed" in l or "Error" in l))
r("npx tsx --env-file=.env.local scripts/seed.ts")
