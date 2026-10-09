"""L'ASSEMBLEUR : description → app qui tourne, sans écrire une ligne de code pour cette app.

Chaque étape lit une fiche et en écrit une autre dans runs/<n°>/ (règles 6 et 7 : le plan vient du
programme, chaque fichier sait d'où il vient) et laisse un événement dans le journal de fabrication.
"""
from __future__ import annotations

import json
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

from .blocs import blocs_de
from .blocs import controle as controle_architecture
from .description import Description
from .journal import Journal
from .matrice import compute_matrix
from .traduire.depart import traduire_depart
from .traduire.ecran import traduire_droits, traduire_notice
from .traduire.schema import traduire_schema

RACINE = Path(__file__).resolve().parents[1]
SQUELETTE = Path(__file__).resolve().parent / "modele-app"
RUNS = RACINE / "runs"
CONTENEUR_BASE = "temporal-postgresql"
IGNORES = shutil.ignore_patterns("node_modules", ".next", "*.tsbuildinfo", ".env*", "test-results")


def _cmd(args: str, cwd: Path, log: Path, env: dict | None = None) -> str:
    """Lance une commande ; sa sortie complète va dans logs/ ; en cas d'échec, la fin est remontée."""
    import os
    res = subprocess.run(args, cwd=cwd, shell=True, capture_output=True, text=True, encoding="utf-8",
                         errors="replace", env={**os.environ, **(env or {})})
    log.write_text(f"$ {args}\n\n{res.stdout}\n{res.stderr}", encoding="utf-8")
    if res.returncode != 0:
        fin = "\n".join((res.stdout + "\n" + res.stderr).strip().splitlines()[-15:])
        raise RuntimeError(f"« {args} » a échoué (journal : {log}) :\n{fin}")
    return res.stdout


def _port_libre() -> int:
    import socket
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class _serveur:
    """Démarre l'app le temps des tests d'écran, puis l'arrête (avec tous ses processus)."""

    def __init__(self, app: Path, port: int, log: Path):
        self.app, self.port, self.log = app, port, log

    def __enter__(self):
        import time
        import urllib.request
        self.f = self.log.open("w", encoding="utf-8")
        self.p = subprocess.Popen(f"npx next start -p {self.port}", cwd=self.app, shell=True, stdout=self.f, stderr=subprocess.STDOUT)
        for _ in range(60):
            try:
                urllib.request.urlopen(f"http://localhost:{self.port}/", timeout=3)
                return self
            except Exception:
                time.sleep(1)
        self.__exit__(None, None, None)
        raise RuntimeError(f"l'app ne répond pas sur le port {self.port} (journal : {self.log})")

    def __exit__(self, *exc):
        subprocess.run(f"taskkill /PID {self.p.pid} /T /F", shell=True, capture_output=True)
        self.f.close()


def fabriquer(chemin_description: Path) -> Path:
    brut = json.loads(chemin_description.read_text(encoding="utf-8"))
    nom = brut.get("app", {}).get("nom", "app")
    run = RUNS / f"{datetime.now():%Y%m%d-%H%M%S}-{nom}"
    (run / "logs").mkdir(parents=True)
    journal = Journal(run, total=10)
    print(f"Fabrication : {run.relative_to(RACINE)}\n")

    with journal.etape("Lire la description (et contrôler l'architecture de l'usine)") as e:
        incomplet = controle_architecture()        # l'usine ne fabrique pas avec un catalogue de blocs incomplet
        if incomplet:
            raise RuntimeError("architecture de l'usine incomplète (python -m usine carte) :\n- " + "\n- ".join(incomplet))
        desc = Description.model_validate(brut)       # forme stricte (règle 3)
        (run / "01-description.json").write_text(desc.model_dump_json(indent=2), encoding="utf-8")
        blocs = blocs_de(desc)
        e["resume"] = (f"{len(desc.acces.actors)} rôles, {len(desc.acces.entities)} fiches, "
                       f"{sum(len(c) for c in desc.champs.values())} champs ; {len(blocs)} blocs utilisés")

    with journal.etape("Calculer la matrice") as e:
        m = compute_matrix(desc.acces)
        if m.errors:
            raise ValueError("matrice refusée :\n- " + "\n- ".join(m.errors))
        (run / "02-matrice.json").write_text(m.model_dump_json(indent=2), encoding="utf-8")
        actives = [c for c in m.cells if c.see != "none" or c.see_via or c.create != "no" or c.transitions]
        e["resume"] = f"{len(actives)} cases actives, {len(m.auto_links)} lien(s) automatique(s)"

    with journal.etape("Traduire") as e:
        produits = {
            "zenstack/schema.zmodel": traduire_schema(desc, m),
            "lib/notice.ts": traduire_notice(desc, m),
            "lib/droits.ts": traduire_droits(desc, m),
            "depart.json": json.dumps(traduire_depart(desc, m), ensure_ascii=False, indent=2),
            # ce que les tests livrés avec l'app vérifient : SA description et SA matrice
            "verification/description.json": desc.model_dump_json(indent=2),
            "verification/matrice.json": m.model_dump_json(indent=2),
        }
        trad = run / "03-traduction"
        for chemin, contenu in produits.items():
            (trad / chemin).parent.mkdir(parents=True, exist_ok=True)
            (trad / chemin).write_text(contenu, encoding="utf-8")
        nb_regles = produits["zenstack/schema.zmodel"].count("@@allow") + produits["zenstack/schema.zmodel"].count("@@deny")
        e["resume"] = f"{len(produits)} fichiers de données ; {nb_regles} règles d'accès"

    app = run / "app"
    with journal.etape("Assembler (squelette fixe + fichiers produits)") as e:
        shutil.copytree(SQUELETTE, app, ignore=IGNORES)
        for chemin, contenu in produits.items():
            (app / chemin).parent.mkdir(parents=True, exist_ok=True)
            (app / chemin).write_text(contenu, encoding="utf-8")
        nb = sum(1 for p in app.rglob("*") if p.is_file())
        e["resume"] = f"{nb} fichiers ; {len(produits)} produits, le reste fixe"

    with journal.etape("Installer les dépendances (versions figées)") as e:
        _cmd("npm ci --prefer-offline --no-audit --no-fund", app, run / "logs" / "installer.log")
        e["resume"] = "installé depuis le fichier de verrouillage du squelette"

    with journal.etape("Générer le code d'accès et créer la base") as e:
        _cmd("npx zen generate --schema zenstack/schema.zmodel -o zenstack --silent", app, run / "logs" / "generer.log")
        base = f"usine_{run.name.replace('-', '_')}"
        _cmd(f'docker exec {CONTENEUR_BASE} psql -U temporal -d postgres -c "CREATE DATABASE {base}"', app,
             run / "logs" / "base.log")
        url = f"postgresql://temporal:temporal@localhost:5432/{base}"
        # TZ=UTC : le serveur compte le temps comme la base. Sinon une date relue puis comparée
        # (« la date de création ne change pas ») se décale du fuseau de la machine (trouvé en N1.1).
        (app / ".env.local").write_text(f"DATABASE_URL={url}\nTZ=UTC\n", encoding="ascii")
        _cmd("npx zen db push --schema zenstack/schema.zmodel", app, run / "logs" / "tables.log", env={"DATABASE_URL": url})
        e["resume"] = f"base « {base} » créée (neuve : jamais de remise à zéro)"

    with journal.etape("Données de départ") as e:
        sortie = _cmd("npx tsx --env-file=.env.local scripts/seed.ts", app, run / "logs" / "depart.log")
        e["resume"] = sortie.strip().splitlines()[-1] if sortie.strip() else "fait"

    with journal.etape("Construire l'app (compilation et typage compris)") as e:
        _cmd("npx next build", app, run / "logs" / "construire.log", env={"NEXT_TELEMETRY_DISABLED": "1"})
        e["resume"] = "compilée sans erreur"

    verdicts = {}
    with journal.etape("Vérifier les règles (testeur par rôle, sur la base)") as e:
        sortie = _cmd("npx tsx --env-file=.env.local verification/testeur.mts", app, run / "logs" / "regles.log")
        bilan = next((l.strip() for l in sortie.splitlines() if "conformes" in l), "")
        ok, total = (int(x) for x in bilan.split()[0].split("/")) if bilan else (0, 1)
        verdicts["regles"] = bilan
        if ok != total:
            raise RuntimeError(f"règles non conformes : {bilan} (détail : logs/regles.log)")
        e["resume"] = bilan

    with journal.etape("Vérifier les écrans (tests par rôle dans un navigateur)") as e:
        _cmd("npx tsx --env-file=.env.local scripts/seed.ts", app, run / "logs" / "depart-ecrans.log")
        port = _port_libre()
        with _serveur(app, port, run / "logs" / "serveur.log"):
            sortie = _cmd("npx playwright test", app, run / "logs" / "ecrans.log", env={"BASE_URL": f"http://localhost:{port}"})
        bilan = next((l.strip() for l in reversed(sortie.splitlines()) if "passed" in l), "")
        sautes = next((l.strip() for l in reversed(sortie.splitlines()) if "skipped" in l), "")
        verdicts["ecrans"] = bilan + (f" ; {sautes}" if sautes else "")
        e["resume"] = verdicts["ecrans"]
        _cmd("npx tsx --env-file=.env.local scripts/seed.ts", app, run / "logs" / "depart-final.log")  # base propre à la livraison

    rapport = {"run": run.name, "description": str(chemin_description), "verdicts": verdicts, "blocs": blocs,
               "fini": datetime.now().isoformat(timespec="seconds")}
    print(f"\nBlocs utilisés : {', '.join(blocs)}")
    (run / "99-rapport.json").write_text(json.dumps(rapport, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nApp fabriquée : {app.relative_to(RACINE)}")
    print(f"Pour la lancer : python -m usine demarrer {run.relative_to(RACINE)}")
    return run
