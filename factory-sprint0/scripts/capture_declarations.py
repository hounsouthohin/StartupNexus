"""
scripts/capture_declarations.py
───────────────────────────────
Capture des déclarations étalons du harnais (USINE.md, phase 1).

Lance l'architect SEUL (sans Temporal, sans génération ni build) sur des briefs et
enregistre chaque déclaration dans harness/declarations/<projet>.json.
Coût : les appels LLM de l'architect (≈5 par brief, gpt-4o-mini).

Usage (dans le conteneur factory-worker) :
    python scripts/capture_declarations.py --briefs scripts/test_full_pipeline.json
    python scripts/capture_declarations.py --briefs scripts/test_expansion_d.json --only abo-tracker
    python scripts/capture_declarations.py --briefs ... --force      # remplace un étalon existant

Un étalon existant n'est jamais remplacé sans --force : le recapturer change la référence.
"""
from __future__ import annotations

import argparse
import asyncio
import sys
import uuid
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

HARNESS_DECLARATIONS = _ROOT / "harness" / "declarations"


async def _capture_one(project_name: str, brief: dict, stack_id: str) -> dict:
    from agents.architect import create_architect_agent
    from agents.shared_tools import set_run_id, set_stack_id
    from workflows.activities.architect_activity import build_architect_initial_state

    run_id = f"capture-{uuid.uuid4().hex[:8]}"
    set_run_id(run_id)
    set_stack_id(stack_id)
    agent = create_architect_agent()
    final_state = await agent.ainvoke(build_architect_initial_state(brief, project_name, stack_id, run_id))
    return {"run_id": run_id, "project_spec": final_state.get("project_spec") or {}}


async def main() -> int:
    parser = argparse.ArgumentParser(description="Capture des déclarations étalons (architect seul)")
    parser.add_argument("--briefs", required=True, help="Fichier JSON de briefs (même format que run_batch.py)")
    parser.add_argument("--only", action="append", default=[], help="Ne capturer que ce projet (répétable)")
    parser.add_argument("--force", action="store_true", help="Remplacer un étalon existant")
    parser.add_argument("--stack", default="nextjs-clerk-prisma")
    args = parser.parse_args()

    from dotenv import load_dotenv
    load_dotenv()
    from agents.llm_provider import validate_llm_env
    ok, msg = validate_llm_env()
    if not ok:
        print(f"✗ Configuration LLM absente : {msg}")
        return 1

    from scripts.run_batch import _load_projects_from_briefs_file
    from agents.declaration_store import build_declaration, save_declaration

    projects = _load_projects_from_briefs_file(args.briefs)
    if args.only:
        projects = [p for p in projects if p["project_name"] in args.only]
        if not projects:
            print(f"✗ Aucun projet de {args.briefs} ne correspond à {args.only}")
            return 1

    failures = 0
    for item in projects:
        name, brief = item["project_name"], item["brief"]
        dest = HARNESS_DECLARATIONS / f"{name}.json"
        if dest.exists() and not args.force:
            print(f"• {name} : étalon déjà présent ({dest.name}) — ignoré (utiliser --force pour le remplacer)")
            continue
        print(f"▶ {name} : architect en cours…", flush=True)
        try:
            captured = await _capture_one(name, brief, args.stack)
        except Exception as e:
            failures += 1
            print(f"  ✗ échec de l'architect : {e}")
            continue
        spec = captured["project_spec"]
        if not spec.get("models"):
            failures += 1
            print("  ✗ déclaration sans modèles — non enregistrée")
            continue
        save_declaration(build_declaration(name, brief, spec, run_id=captured["run_id"], stack_id=args.stack), dest)
        roles = ((spec.get("enriched_spec") or {}).get("roles") or {}).get("roles") or []
        print(
            f"  ✓ {dest.relative_to(_ROOT)} — {len(spec.get('models', []))} modèles, "
            f"{len(spec.get('pages', []))} pages, rôles={roles or '—'}, "
            f"non couverts={len(spec.get('unsupported') or [])}"
        )

    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
