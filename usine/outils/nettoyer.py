"""NETTOYAGE de runs/ (accord de l'utilisateur, 13 oct) : on garde les compréhensions, les répétitions (résumés),
le tableau, et la DERNIÈRE app de chaque brief (celles de la répétition donnée + les exemples nommés) ; on supprime les
autres apps et leurs bases de données. Usage : python nettoyer.py <répétition à garder> <app à garder>… [--vraiment]"""
import json, subprocess, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
RUNS = Path(r"C:\Users\BAMBARA Arthur\Desktop\StartupNexus\runs")
args = [a for a in sys.argv[1:] if a != "--vraiment"]
vraiment = "--vraiment" in sys.argv
rep, extra = RUNS / args[0], set(args[1:])
garder = set(extra)
for l in json.loads((rep / "repetition.json").read_text(encoding="utf-8")):
    for k in ("essai", "variante"):
        if (l.get(k) or {}).get("run"):
            garder.add(l[k]["run"])
supprimer, octets = [], 0
for d in sorted(p for p in RUNS.iterdir() if p.is_dir()):
    n = d.name
    if n.endswith("-comprendre") or "-repetition-" in n or n == "tableau" or n in garder:
        continue
    supprimer.append(d)
    octets += sum(f.stat().st_size for f in d.rglob("*") if f.is_file())
print(f"à garder : {len(garder)} apps ; à supprimer : {len(supprimer)} dossiers, {octets / 1e9:.1f} Go")
bases = subprocess.run('docker exec temporal-postgresql psql -U temporal -d postgres -tAc "select datname from pg_database where datname like \'usine_%\'"',
                       shell=True, capture_output=True, text=True).stdout.split()
gardees = {"usine_" + g.replace("-", "_") for g in garder}
a_jeter = [b for b in bases if b not in gardees]
print(f"bases : {len(bases)} ; à supprimer : {len(a_jeter)}")
if not vraiment:
    print("(essai à blanc : rien n'a été supprimé — relancer avec --vraiment)")
    sys.exit(0)
for d in supprimer:
    subprocess.run(f'cmd /c rmdir /s /q "{d}"', shell=True, capture_output=True)
for b in a_jeter:
    subprocess.run(f'docker exec temporal-postgresql psql -U temporal -d postgres -c "DROP DATABASE IF EXISTS {b}"',
                   shell=True, capture_output=True)
restants = [d for d in supprimer if d.exists()]
print(f"supprimés : {len(supprimer) - len(restants)} dossiers ({len(restants)} non supprimés), {len(a_jeter)} bases")
