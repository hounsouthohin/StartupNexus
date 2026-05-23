"""
run_test_galerie.py — Script de test end-to-end pour "galerie-projets".

App conçue pour couvrir TOUTE la factory en un seul run :
  Level A  : 2 modèles (Project + Tech), FK, slug @unique, status enum
  Level B  : /dashboard (custom privé), /projects (liste publique)
  Templates: pages publiques SANS boutons admin (test fix auth_required)
  Services : getPublicAll() filtré par status='published', getBySlug()
  Contract : Contract Generator → appels de service précis par page custom

Usage :
  cd factory-sprint0
  python scripts/run_test_galerie.py

  Options :
    --no-extract  : ne pas extraire le ZIP après le run
    --out-dir DIR : répertoire d'extraction (défaut: ../_test_galerie)
    --timeout N   : secondes max d'attente du workflow (défaut: 300)
"""
from __future__ import annotations

import asyncio
import argparse
import json
import os
import subprocess
import sys
import time
import uuid
import zipfile
from pathlib import Path

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from temporalio.client import Client
from config.factory_config import TEMPORAL_ADDRESS
from workflows.todo_pilot_workflow import TodoPilotWorkflow

TASK_QUEUE     = "factory-task-queue"
PROJECT_NAME   = "galerie-projets"
DOCKER_CONTAINER = "factory-worker"
DOCKER_ZIP_PATH  = f"/app/generated-projects/exports/{PROJECT_NAME}.zip"

# ── Brief ──────────────────────────────────────────────────────────────────────
# Format naturel (style test_all_levels.json) — description seule.
# L'architect infère modèles, pages, routes et enums depuis la description.
#
# Couverture factory ciblée :
#   - Pages publiques (auth=False) : liste projets publiés + détail par slug
#   - Dashboard privé custom : résumé activité
#   - CRUD privé complet : créer / modifier / supprimer projets et technos
#   - Enum status (draft/published/archived)
#   - FK relation : Project → Tech
#   - Slug @unique sur Project
# ──────────────────────────────────────────────────────────────────────────────
BRIEF = {
    "description": (
        "Une galerie de projets pour développeur indépendant. "
        "L'auteur publie ses projets personnels avec un titre, une description, "
        "un slug unique (pour l'URL publique) et un statut géré par un enum "
        "(draft, published, archived). "
        "Les visiteurs parcourent les projets publiés sur /projects et consultent "
        "chaque projet via son URL lisible (ex: /projects/mon-projet) sans se connecter. "
        "Le développeur gère ses projets depuis son dashboard privé : il peut créer, "
        "modifier et supprimer ses projets. "
        "Chaque projet peut être associé à une technologie principale (nom de la techno). "
        "Le dashboard affiche un résumé de l'activité — projets publiés vs total — "
        "avec des liens vers la gestion des projets et des technologies."
    ),
}

# ── Workflow ───────────────────────────────────────────────────────────────────

async def run_workflow(timeout: int) -> dict:
    run_id = str(uuid.uuid4())
    workflow_id = f"todo-pilot-{PROJECT_NAME}-{run_id[:8]}"

    print(f"\n{'='*60}")
    print(f"  GALERIE-PROJETS — Test factory end-to-end")
    print(f"  Workflow ID : {workflow_id}")
    print(f"  Temporal    : {TEMPORAL_ADDRESS}")
    print(f"{'='*60}\n")

    client = await Client.connect(TEMPORAL_ADDRESS)

    payload = {
        "project_name": PROJECT_NAME,
        "run_id":        run_id,
        "brief":         BRIEF,
        "stack_id":      "nextjs-clerk-prisma",
    }

    print("→ Démarrage du workflow...")
    t0 = time.time()

    handle = await client.start_workflow(
        TodoPilotWorkflow.run,
        payload,
        id=workflow_id,
        task_queue=TASK_QUEUE,
    )

    print(f"→ Workflow démarré. Attente (timeout={timeout}s)...\n")

    try:
        result = await asyncio.wait_for(handle.result(), timeout=timeout)
    except asyncio.TimeoutError:
        print(f"\n⚠️  Timeout {timeout}s dépassé — workflow en cours dans Temporal.")
        return {}

    elapsed = round(time.time() - t0, 1)
    return {"result": result, "elapsed": elapsed, "workflow_id": workflow_id}


def extract_zip(out_dir: str) -> bool:
    out_path = Path(out_dir)
    zip_local = out_path.parent / f"{PROJECT_NAME}.zip"

    print(f"\n→ Extraction ZIP depuis Docker ({DOCKER_CONTAINER})...")
    cp = subprocess.run(
        ["docker", "cp", f"{DOCKER_CONTAINER}:{DOCKER_ZIP_PATH}", str(zip_local)],
        capture_output=True, text=True,
    )
    if cp.returncode != 0:
        print(f"  ❌ docker cp échoué : {cp.stderr.strip()}")
        print(f"     Manuel : docker cp {DOCKER_CONTAINER}:{DOCKER_ZIP_PATH} .")
        return False

    out_path.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_local, "r") as z:
        z.extractall(out_path)
    zip_local.unlink()
    print(f"  ✓ Extrait → {out_path}/")
    return True


def print_summary(data: dict, out_dir: str) -> None:
    result   = data.get("result", {})
    elapsed  = data.get("elapsed", "?")
    ar       = result.get("activity_results", {})
    dev      = ar.get("dev_test", {})
    rm       = dev.get("run_metric", {})
    meta     = dev.get("metadata", {})
    review   = ar.get("review", {})

    print(f"\n{'='*60}")
    print(f"  RÉSULTAT — {elapsed}s")
    print(f"{'='*60}")
    print(f"  Build        : {result.get('build_status','?')}")
    print(f"  Fichiers     : {meta.get('total_files','?')}")
    print(f"  Requirements : {meta.get('requirements_met','?')}/{meta.get('requirements_total','?')}")
    print(f"  User flows   : {meta.get('user_flows_covered','?')}/{meta.get('user_flows_total','?')}")
    print(f"  TSC ok       : {rm.get('tsc_ok_by_activity','?')}")
    print(f"  Itérations   : {rm.get('iterations','?')}")
    print(f"  Review       : {review.get('verdict','?')} (security={review.get('security_score','?')})")

    findings = review.get("findings", [])
    if findings:
        print(f"\n  Findings ({len(findings)}) :")
        for f in findings[:5]:
            sev  = f.get("severity", "?")
            typ  = f.get("type", "?")
            file = f.get("file", "?")
            print(f"    [{sev}] {typ} — {file}")

    err = rm.get("last_build_error", "")
    if err:
        print(f"\n  Dernière erreur build :\n    {err[:250]}")

    print(f"\n  Projet extrait → {out_dir}/")
    print(f"\n{'='*60}")
    print("  CHECKLIST VALIDATION MANUELLE")
    print(f"{'='*60}")
    print("""
  Level A — Déterminisme :
  [ ] lib/types.ts          — SerializedProject.status = "draft"|"published"|"archived"
  [ ] lib/types.ts          — SerializedProject.tech?: {{ id, name }}  (FK optionnelle)
  [ ] project.service.ts    — getPublicAll() contient where: {{ status: 'published' }}
  [ ] project.service.ts    — getBySlug(slug) présent
  [ ] middleware.ts          — /projects(.*) dans isPublicRoute

  Level B — Templates (test fix auth_required) :
  [ ] app/projects/page-client.tsx      — PAS de bouton "Nouveau" ni colonne "Actions"
  [ ] app/projects/[slug]/page-client.tsx — PAS de bouton "Modifier"

  Level B — Contract Generator :
  [ ] app/dashboard/page.tsx            — appelle projectService.getAll(userId)
  [ ] app/dashboard/page-client.tsx     — props: {{ items: SerializedProject[] }}

  Déployabilité :
  [ ] prisma/schema.prisma   — enum ProjectStatus, slug @unique, PAS de modèle User
  [ ] next build             — 0 erreur TypeScript
""")


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-extract", action="store_true")
    parser.add_argument("--out-dir",  default=str(Path(PROJECT_ROOT).parent / "_test_galerie"))
    parser.add_argument("--timeout",  type=int, default=300)
    args = parser.parse_args()

    data = await run_workflow(args.timeout)
    if not data:
        sys.exit(1)

    if not args.no_extract:
        extract_zip(args.out_dir)

    print_summary(data, args.out_dir)

    build_ok = str(data.get("result", {}).get("build_status", "")).upper() == "SUCCESS"
    sys.exit(0 if build_ok else 1)


if __name__ == "__main__":
    asyncio.run(main())
