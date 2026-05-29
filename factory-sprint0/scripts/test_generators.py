"""
scripts/test_generators.py
──────────────────────────
Test rapide des générateurs Level A — sans LLM, sans Temporal, sans Docker.

Usage :
    python -m scripts.test_generators                        # brief project-hub par défaut
    python -m scripts.test_generators --spec fixtures/my.json
    python -m scripts.test_generators --tsc                  # lance tsc --noEmit après génération
    python -m scripts.test_generators --keep                 # conserve le dossier tmp après le test

Ce script charge une fixture spec JSON, lance tous les générateurs déterministes,
écrit les fichiers dans un dossier temporaire, et vérifie la cohérence de sortie.
Aucun token LLM consommé. Durée : ~5-15 secondes.
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

# ── Path setup ────────────────────────────────────────────────────────────────
_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("test_generators")

_FIXTURES_DIR = Path(__file__).parent / "fixtures"
_DEFAULT_FIXTURE = _FIXTURES_DIR / "project_hub_spec.json"


# ── Helpers ───────────────────────────────────────────────────────────────────

def _load_spec(spec_path: Path) -> dict:
    with open(spec_path, encoding="utf-8") as f:
        return json.load(f)


def _build_project_spec(raw: dict):
    """Construit un ProjectSpec depuis le dict fixture (même chemin que planner_node)."""
    from agents.architect import _parse_model_str
    from agents.project_spec import ProjectSpec, AppPage, ApiRoute
    from agents.stacks.base import get_adapter_for_stack

    stack_id = raw.get("stack_id", "nextjs-clerk-prisma")
    project_name = raw.get("project_name", "test-project")

    models = []
    seen: set[str] = set()
    for m_str in raw.get("models", []):
        m = _parse_model_str(str(m_str))
        if m.name not in seen:
            models.append(m)
            seen.add(m.name)
    models = get_adapter_for_stack(stack_id).inject_relations(models)

    pages = []
    seen_paths: set[str] = set()
    for pg in raw.get("pages", []):
        path = pg.get("path", "/")
        if path not in seen_paths:
            pages.append(AppPage(
                path=path,
                auth_required=bool(pg.get("auth", True)),
                model=pg.get("model") or None,
                page_type=pg.get("page_type", "custom"),
            ))
            seen_paths.add(path)
    if not any(p.path == "/" for p in pages):
        pages.insert(0, AppPage(path="/", auth_required=False))

    routes = []
    for rt in raw.get("routes", []):
        if isinstance(rt, dict):
            routes.append(ApiRoute(method=rt.get("method", "GET"), path=rt.get("path", "/")))  # type: ignore

    return ProjectSpec(
        project_name=project_name,
        stack_id=stack_id,
        description=raw.get("description", ""),
        models=models,
        routes=routes,
        pages=pages,
        pages_detail=raw.get("pages_detail", {}),
        user_flows=raw.get("user_flows", []),
        enums=raw.get("enums", {}),
        ui_labels=raw.get("ui_labels", {}),
        title_plurals=raw.get("title_plurals", {}),
        enum_value_labels=raw.get("enum_value_labels", {}),
    ).with_fingerprint()


def _run_generators(spec_obj, workdir: str) -> dict[str, list[str]]:
    """Lance tous les générateurs Level A. Retourne {categorie: [fichiers générés]}."""
    from agents.stacks.nextjs_clerk_prisma.dev_model_context import build_all_contexts
    from agents.stack_config import load_stack_config
    from agents.stacks.nextjs_clerk_prisma.dev_file_ops import write_template_files

    results: dict[str, list[str]] = {
        "templates": [],
        "schema": [],
        "types": [],
        "schemas": [],
        "services": [],
        "actions": [],
        "pages": [],
        "page_clients": [],
        "parent_details": [],
        "feature_modules": [],
        "navigation": [],
        "middleware": [],
        "errors": [],
    }

    stack_id = spec_obj.stack_id or "nextjs-clerk-prisma"
    stack_cfg = load_stack_config(stack_id)

    # 1. Fichiers template (package.json, layout, etc.)
    try:
        written = write_template_files(workdir, stack_cfg, spec_obj.project_name, stack_id, spec=spec_obj.model_dump())
        results["templates"] = list(written.keys())
    except Exception as e:
        results["errors"].append(f"write_template_files: {e}")

    # 2. Schema Prisma
    try:
        schema = spec_obj.to_prisma_schema_block()
        schema_path = os.path.join(workdir, "prisma", "schema.prisma")
        os.makedirs(os.path.dirname(schema_path), exist_ok=True)
        with open(schema_path, "w", encoding="utf-8") as f:
            f.write(schema)
        results["schema"] = ["prisma/schema.prisma"]
    except Exception as e:
        results["errors"].append(f"schema: {e}")

    # 3. ModelGenerationContext (source unique de vérité pour tous les générateurs)
    model_contexts = {}
    try:
        model_contexts = build_all_contexts(spec_obj)
    except Exception as e:
        results["errors"].append(f"build_all_contexts: {e}")

    # 4. Middleware
    try:
        from agents.stacks.nextjs_clerk_prisma.dev_middleware_generator import generate_middleware
        mw = generate_middleware(spec_obj, workdir)
        results["middleware"] = list(mw.keys())
    except Exception as e:
        results["errors"].append(f"middleware: {e}")

    # 5. Navigation
    try:
        from agents.stacks.nextjs_clerk_prisma.dev_navigation_generator import generate_navigation
        nav = generate_navigation(spec_obj, workdir)
        results["navigation"] = list(nav.keys())
    except Exception as e:
        results["errors"].append(f"navigation: {e}")

    # 6. Pages (page.tsx déterministes)
    try:
        from agents.stacks.nextjs_clerk_prisma.dev_pages_generator import (
            generate_page_stubs, generate_edit_page_stubs,
            generate_loading_files, generate_error_files, generate_root_page_if_needed,
        )
        generate_root_page_if_needed(spec_obj, workdir)
        pages = generate_page_stubs(spec_obj, workdir, contexts=model_contexts)
        edit_pages = generate_edit_page_stubs(spec_obj, workdir, contexts=model_contexts)
        generate_loading_files(spec_obj, workdir)
        generate_error_files(spec_obj, workdir)
        results["pages"] = list(pages.keys()) + list(edit_pages.keys())
    except Exception as e:
        results["errors"].append(f"pages: {e}")

    # 7. lib/types.ts
    try:
        from agents.stacks.nextjs_clerk_prisma.dev_types_generator import generate_types_file
        t = generate_types_file(spec_obj, workdir, contexts=model_contexts)
        results["types"] = [t.path]
    except Exception as e:
        results["errors"].append(f"types: {e}")

    # 8. lib/schemas.ts
    try:
        from agents.stacks.nextjs_clerk_prisma.dev_zod_generator import generate_schemas_file
        s = generate_schemas_file(spec_obj, workdir, contexts=model_contexts)
        if s:
            results["schemas"] = [s.path]
    except Exception as e:
        results["errors"].append(f"schemas: {e}")

    # 9. Services
    try:
        from agents.stacks.nextjs_clerk_prisma.dev_service_generator import generate_service_files
        svcs = generate_service_files(spec_obj, workdir, contexts=model_contexts)
        results["services"] = list(svcs.keys())
    except Exception as e:
        results["errors"].append(f"services: {e}")

    # 10. Actions
    try:
        from agents.stacks.nextjs_clerk_prisma.dev_actions_generator import generate_action_files
        acts = generate_action_files(spec_obj, workdir, model_contexts=model_contexts)
        results["actions"] = list(acts.keys())
    except Exception as e:
        results["errors"].append(f"actions: {e}")

    # 11. Page-clients (Jinja2)
    try:
        from agents.stacks.nextjs_clerk_prisma.dev_form_generator import (
            generate_all_page_clients, generate_parent_detail_pages,
        )
        clients = generate_all_page_clients(spec_obj, model_contexts, workdir)
        parent_detail = generate_parent_detail_pages(spec_obj, model_contexts, workdir)
        results["page_clients"] = list(clients.keys())
        results["parent_details"] = list(parent_detail.keys())
    except Exception as e:
        results["errors"].append(f"page_clients: {e}")

    # 12. Feature modules
    try:
        from agents.stacks.nextjs_clerk_prisma.feature_module import (
            load_feature_modules, run_feature_modules,
        )
        _fm_names = stack_cfg.get("feature_modules", [])
        load_feature_modules(_fm_names, package="agents.stacks.nextjs_clerk_prisma")
        fm_files = run_feature_modules(spec_obj, model_contexts, None, workdir)
        results["feature_modules"] = list(fm_files.keys())
    except Exception as e:
        results["errors"].append(f"feature_modules: {e}")

    return results


def _count_files(workdir: str) -> int:
    count = 0
    for root, dirs, files in os.walk(workdir):
        dirs[:] = [d for d in dirs if d not in {"node_modules", ".next", ".git"}]
        count += len(files)
    return count


def _run_tsc(workdir: str) -> tuple[bool, str]:
    """Lance tsc --noEmit dans le workdir. Retourne (ok, output)."""
    try:
        r = subprocess.run(
            "npx tsc --noEmit",
            shell=True, capture_output=True, text=True,
            timeout=60, cwd=workdir,
        )
        out = (r.stdout + r.stderr).strip()
        return r.returncode == 0, out
    except subprocess.TimeoutExpired:
        return False, "TIMEOUT (>60s)"
    except Exception as e:
        return False, f"tsc unavailable: {e}"


def _print_section(title: str, items: list[str], color: str = "") -> None:
    reset = "\033[0m"
    print(f"\n  {color}{title}{reset} ({len(items)} fichiers)")
    for item in items[:8]:
        print(f"    • {item}")
    if len(items) > 8:
        print(f"    … +{len(items) - 8} autres")


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(description="Test rapide des générateurs Level A")
    parser.add_argument("--spec", default=str(_DEFAULT_FIXTURE), help="Chemin vers la fixture spec JSON")
    parser.add_argument("--tsc", action="store_true", help="Lancer tsc --noEmit après génération")
    parser.add_argument("--keep", action="store_true", help="Conserver le dossier temporaire")
    args = parser.parse_args()

    GREEN  = "\033[32m"
    RED    = "\033[31m"
    YELLOW = "\033[33m"
    CYAN   = "\033[36m"
    BOLD   = "\033[1m"
    RESET  = "\033[0m"

    spec_path = Path(args.spec)
    if not spec_path.is_absolute():
        spec_path = Path(__file__).parent / args.spec
    if not spec_path.exists():
        print(f"{RED}✗ Fixture introuvable : {spec_path}{RESET}")
        return 1

    print(f"\n{BOLD}═══ Test Générateurs Level A ═══{RESET}")
    print(f"  Fixture : {spec_path.name}")

    # Charger la spec
    t0 = time.perf_counter()
    raw = _load_spec(spec_path)
    spec_obj = _build_project_spec(raw)
    print(f"  Spec    : {len(spec_obj.models)} modèles, {len(spec_obj.pages)} pages, {len(spec_obj.enums)} enums")

    # Créer le workdir temporaire
    workdir = tempfile.mkdtemp(prefix="factory_test_")
    print(f"  Workdir : {workdir}")

    try:
        # Lancer les générateurs
        print(f"\n{CYAN}▶ Génération...{RESET}")
        results = _run_generators(spec_obj, workdir)
        elapsed = time.perf_counter() - t0

        # Afficher les résultats par catégorie
        categories = [
            ("Templates stack",   results["templates"],      CYAN),
            ("Schema Prisma",     results["schema"],         CYAN),
            ("lib/types.ts",      results["types"],          CYAN),
            ("lib/schemas.ts",    results["schemas"],        CYAN),
            ("Services DAL",      results["services"],       CYAN),
            ("Server Actions",    results["actions"],        CYAN),
            ("Pages (page.tsx)",  results["pages"],          CYAN),
            ("Page-clients",      results["page_clients"],   CYAN),
            ("Détails parent",    results["parent_details"], CYAN),
            ("Feature modules",   results["feature_modules"], GREEN),
            ("Navigation",        results["navigation"],     CYAN),
            ("Middleware",        results["middleware"],      CYAN),
        ]
        total_files = sum(len(v) for k, v in results.items() if k != "errors")
        for label, files, color in categories:
            if files:
                _print_section(label, files, color)

        total_on_disk = _count_files(workdir)
        print(f"\n  {BOLD}Total généré{RESET} : {total_files} fichiers suivis | {total_on_disk} sur disque")
        print(f"  {BOLD}Durée{RESET}        : {elapsed:.1f}s")

        # Erreurs générateurs
        has_errors = bool(results["errors"])
        if has_errors:
            print(f"\n{RED}✗ Erreurs générateurs :{RESET}")
            for e in results["errors"]:
                print(f"    • {e}")
        else:
            print(f"\n  {GREEN}✓ Tous les générateurs ont tourné sans erreur{RESET}")

        # TSC optionnel
        tsc_ok = None
        if args.tsc:
            print(f"\n{CYAN}▶ TypeScript check (tsc --noEmit)...{RESET}")
            tsc_ok, tsc_out = _run_tsc(workdir)
            if tsc_ok:
                print(f"  {GREEN}✓ tsc OK — aucune erreur TypeScript{RESET}")
            else:
                print(f"  {RED}✗ tsc FAILED{RESET}")
                if tsc_out:
                    lines = tsc_out.splitlines()[:20]
                    for line in lines:
                        print(f"    {line}")
                    if len(tsc_out.splitlines()) > 20:
                        print(f"    … +{len(tsc_out.splitlines()) - 20} lignes supplémentaires")

        # Résultat final
        print()
        if has_errors or tsc_ok is False:
            print(f"{RED}{BOLD}✗ BUILD_FAILED{RESET} — corriger les erreurs ci-dessus")
            return 1
        else:
            print(f"{GREEN}{BOLD}✓ GENERATORS_OK{RESET}" + (" + TSC_OK" if tsc_ok else " (tsc non lancé — ajouter --tsc)"))
            return 0

    finally:
        if not args.keep:
            shutil.rmtree(workdir, ignore_errors=True)
        else:
            print(f"\n  Workdir conservé : {workdir}")


if __name__ == "__main__":
    sys.exit(main())
