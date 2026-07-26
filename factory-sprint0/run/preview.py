"""
run/preview.py — cœur du PREVIEW automatique (Scène-B, Option B — 25 Juil 2026).
──────────────────────────────────────────────────────────────────────────────

Tourne DANS le worker. Prépare une app générée pour qu'elle soit ouvrable :
  1. crée une base dédiée (via le SDK Docker — le worker n'a pas psql, mais pilote
     le conteneur postgres) ;
  2. pousse le schéma (`npx prisma db push --url`) ;
  3. sème les données de démo (`node prisma/seed.mjs`) ;
  4. lance le serveur `next dev` DÉTACHÉ (il survit à l'activité — une activité finit,
     un serveur reste allumé) et renvoie l'URL.

Chaque commande a été validée à la main via l'Option A (scripts/preview.ps1) : l'activité
n'emballe que du connu. Le lancement + connexion Clerk reste le seul point non testable
sans navigateur (même mur qu'en Option A).
"""
from __future__ import annotations

import logging
import os
import subprocess

logger = logging.getLogger(__name__)

_PG_CONTAINER = "temporal-postgresql"
_PG_USER = "temporal"
_PG_HOST = "temporal-postgresql"
_PREVIEW_PORT = int(os.getenv("PREVIEW_PORT", "3100"))


def _db_name(project: str) -> str:
    return "preview_" + "".join(c for c in project if c.isalnum())


def _create_db(name: str) -> None:
    """(Re)crée une base propre en pilotant le conteneur postgres via le SDK Docker."""
    import docker  # déjà dans requirements.txt

    client = docker.from_env()
    pg = client.containers.get(_PG_CONTAINER)
    pg.exec_run(["dropdb", "-U", _PG_USER, "--if-exists", name])
    r = pg.exec_run(["createdb", "-U", _PG_USER, name])
    if r.exit_code != 0:
        raise RuntimeError(f"createdb {name} a échoué : {(r.output or b'').decode()[:200]}")


def _kill_previous_server(port: int) -> None:
    """Tue un éventuel `next dev` précédent sur ce port (un seul preview vivant à la fois).

    Le worker n'a NI pkill NI ps (image minimale) — on scanne /proc directement en Python,
    donc aucune dépendance externe. Fiable et portable.
    """
    import signal

    _needle_port = f"-p {port}"
    for _pid in os.listdir("/proc"):
        if not _pid.isdigit():
            continue
        try:
            with open(f"/proc/{_pid}/cmdline", "rb") as f:
                _cmd = f.read().replace(b"\x00", b" ").decode(errors="ignore")
        except Exception:
            continue
        if "next" in _cmd and "dev" in _cmd and _needle_port in _cmd:
            try:
                os.kill(int(_pid), signal.SIGTERM)
                logger.info("[preview] serveur précédent arrêté (pid %s)", _pid)
            except Exception as e:
                logger.warning("[preview] kill pid %s non bloquant : %s", _pid, e)


def prepare_preview(project: str, seed_user_id: str = "user_demo",
                    port: int | None = None, launch: bool = True) -> dict:
    """Prépare (et lance) le preview d'une app. Retourne {url, db, ...}."""
    port = port or _PREVIEW_PORT
    workdir = os.getenv("FACTORY_WORKDIR", "/app/generated-projects")
    app_dir = os.path.join(workdir, project)
    if not os.path.isdir(app_dir):
        raise RuntimeError(f"projet introuvable : {app_dir}")

    dbname = _db_name(project)
    dburl = f"postgresql://{_PG_USER}:{_PG_USER}@{_PG_HOST}:5432/{dbname}"
    env = {**os.environ, "DATABASE_URL": dburl, "DIRECT_DATABASE_URL": dburl}

    # 1. base
    logger.info("[preview] base %s", dbname)
    _create_db(dbname)

    # 2. schéma
    logger.info("[preview] prisma db push")
    r = subprocess.run(
        ["npx", "prisma", "db", "push", "--url", dburl, "--accept-data-loss"],
        cwd=app_dir, env=env, capture_output=True, text=True, timeout=240,
    )
    if r.returncode != 0:
        raise RuntimeError(f"db push a échoué : {((r.stderr or '') + (r.stdout or ''))[:400]}")

    # 3. seed
    logger.info("[preview] seed (SEED_USER_ID=%s)", seed_user_id)
    r = subprocess.run(
        ["node", "prisma/seed.mjs"],
        cwd=app_dir, env={**env, "SEED_USER_ID": seed_user_id},
        capture_output=True, text=True, timeout=240,
    )
    if r.returncode != 0:
        raise RuntimeError(f"seed a échoué : {((r.stderr or '') + (r.stdout or ''))[:400]}")

    result = {"project": project, "db": dbname, "database_url": dburl,
              "url": f"http://localhost:{port}", "launched": False}

    # 4. serveur détaché (survit à l'activité)
    if launch:
        _kill_previous_server(port)
        server_env = {**env, **{k: v for k, v in os.environ.items() if "CLERK" in k}}
        # Mappage des clés stockées sous les noms CLERK_TEST_* vers les noms que l'app
        # générée lit réellement — seulement si le nom officiel n'est pas déjà défini.
        # Évite à l'opérateur de dupliquer ses clés sous d'autres noms.
        _alias = {
            "NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY": "CLERK_TEST_PUBLISHABLE_KEY",
            "CLERK_SECRET_KEY": "CLERK_TEST_SECRET_KEY",
        }
        for _want, _have in _alias.items():
            if not server_env.get(_want) and os.environ.get(_have):
                server_env[_want] = os.environ[_have]
        _has_pk = bool(server_env.get("NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY"))
        logger.info("[preview] lancement next dev détaché sur :%d (clé publishable=%s)",
                    port, _has_pk)
        # Popen non attendu → le serveur reste allumé après le retour de la fonction.
        subprocess.Popen(
            ["npx", "next", "dev", "-H", "0.0.0.0", "-p", str(port)],
            cwd=app_dir, env=server_env,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        result["launched"] = True

    logger.info("[preview] prêt → %s", result["url"])
    return result
