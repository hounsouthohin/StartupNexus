"""
scripts/harness.py
──────────────────
Le harnais (USINE.md, phase 1) : le filet de sécurité du cœur déterministe.

Pour chaque déclaration étalon de harness/declarations/ :
  1. rejoue les générateurs — `dev_core.generate_core`, LA MÊME fonction que le pipeline —
     sans IA ni Temporal ;
  2. compare les fichiers produits à la référence harness/references/<projet>/ ;
  3. vérifie TypeScript : mêmes commandes de préparation que le pipeline
     (`dev_core.run_pre_run_commands`) puis `tsc --noEmit` (`shared_tools.run_tsc_check`).

Usage (dans le conteneur factory-worker) :
    python scripts/harness.py                   # génération + comparaison + tsc
    python scripts/harness.py --only garage-atlas
    python scripts/harness.py --no-tsc          # génération + comparaison seulement
    python scripts/harness.py --diff            # détail des fichiers modifiés
    python scripts/harness.py --update          # accepte la génération actuelle comme référence
    python scripts/harness.py --keep            # conserve les dossiers générés

Code de sortie 0 : chaque déclaration génère sans erreur, identique à sa référence, et
passe tsc (si demandé). Chaque passage est aussi enregistré dans logs/harness/.

Limites : ne couvre pas ce qui dépend d'un LLM (design brief et page-clients décorés,
pages écrites par l'executor) ; tsc juge les types, pas tout ce que vérifie `next build`.
"""
from __future__ import annotations

import argparse
import asyncio
import difflib
import json
import logging
import os
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

DECLARATIONS_DIR = _ROOT / "harness" / "declarations"
REFERENCES_DIR = _ROOT / "harness" / "references"
REPORTS_DIR = _ROOT / "logs" / "harness"
# Pas /tmp : c'est un tmpfs de ~800 Mo dans le conteneur, node_modules n'y tient pas.
WORK_ROOT = Path(os.getenv("FACTORY_HARNESS_WORKDIR", "/var/tmp/factory_harness"))
_SKIP_DIRS = {"node_modules", ".next", ".git"}

logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(name)s: %(message)s")

GREEN, RED, YELLOW, BOLD, RESET = "\033[32m", "\033[31m", "\033[33m", "\033[1m", "\033[0m"


class _ErrorCapture(logging.Handler):
    """Les générateurs attrapent leurs exceptions et les loggent : on les rend visibles."""

    def __init__(self) -> None:
        super().__init__(level=logging.ERROR)
        self.records: list[str] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append(f"{record.name}: {record.getMessage()}")


def _snapshot(directory: Path) -> dict[str, bytes]:
    files: dict[str, bytes] = {}
    if not directory.is_dir():
        return files
    for path in sorted(directory.rglob("*")):
        rel = path.relative_to(directory)
        if any(part in _SKIP_DIRS for part in rel.parts) or not path.is_file():
            continue
        files[rel.as_posix()] = path.read_bytes()
    return files


def _compare(current: dict[str, bytes], reference: dict[str, bytes]) -> dict[str, list[str]]:
    return {
        "added": sorted(set(current) - set(reference)),
        "removed": sorted(set(reference) - set(current)),
        "changed": sorted(p for p in set(current) & set(reference) if current[p] != reference[p]),
    }


def _write_reference(project: str, files: dict[str, bytes]) -> None:
    ref_dir = REFERENCES_DIR / project
    shutil.rmtree(ref_dir, ignore_errors=True)
    for rel, content in files.items():
        dest = ref_dir / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(content)


def _print_diff(rel: str, old: bytes, new: bytes, max_lines: int = 60) -> None:
    lines = list(difflib.unified_diff(
        old.decode("utf-8", errors="replace").splitlines(),
        new.decode("utf-8", errors="replace").splitlines(),
        fromfile=f"référence/{rel}", tofile=f"actuel/{rel}", lineterm="",
    ))
    for line in lines[:max_lines]:
        print(f"      {line}")
    if len(lines) > max_lines:
        print(f"      … +{len(lines) - max_lines} lignes")


async def _run_one(decl_path: Path, args) -> dict:
    from agents.declaration_store import load_declaration
    from agents.shared_tools import set_stack_id, run_tsc_check
    from agents.stacks.nextjs_clerk_prisma.dev_core import generate_core, run_pre_run_commands

    decl = load_declaration(decl_path)
    project = decl["project_name"]
    spec = decl["project_spec"]
    report: dict = {"project": project, "declaration": decl_path.name}
    print(f"\n{BOLD}▶ {project}{RESET}")

    workdir = WORK_ROOT / project
    shutil.rmtree(workdir, ignore_errors=True)
    workdir.mkdir(parents=True)
    set_stack_id(decl.get("stack_id") or spec.get("stack_id") or "nextjs-clerk-prisma")

    # 1. Génération (même fonction que le pipeline)
    capture = _ErrorCapture()
    logging.getLogger("agents").addHandler(capture)
    t0 = time.perf_counter()
    core = None
    try:
        core = generate_core(spec, str(workdir), project)
    except Exception as e:
        report["crash"] = f"{type(e).__name__}: {e}"
    finally:
        logging.getLogger("agents").removeHandler(capture)
    report["generation_seconds"] = round(time.perf_counter() - t0, 2)
    # Erreurs = ce qui arrête un vrai run (échec des templates, générateur cœur planté,
    # page-client manquant). Alertes = erreurs que les générateurs journalisent sans
    # s'arrêter : elles ne bloquent pas le pipeline, donc pas le harnais non plus, mais
    # elles sont montrées. Les logs de dev_core doublonnent les erreurs : écartés.
    errors: list[str] = []
    if core is not None:
        if core.template_failure:
            errors.append(f"TEMPLATE_FAILURE: {core.template_failure}")
        errors.extend(core.prebuild_errors)
    report["errors"] = errors
    report["alerts"] = list(dict.fromkeys(
        r for r in capture.records if not r.startswith(generate_core.__module__ + ":")
    ))

    files = _snapshot(workdir)
    report["files"] = len(files)
    if report.get("crash"):
        print(f"  {RED}✗ génération plantée : {report['crash']}{RESET}")
    else:
        status = f"{GREEN}sans erreur{RESET}" if not errors else f"{RED}{len(errors)} erreur(s){RESET}"
        print(f"  génération : {len(files)} fichiers en {report['generation_seconds']}s — {status}")
        for err in errors[:10]:
            print(f"    {RED}•{RESET} {err[:300]}")
        for alert in report["alerts"][:10]:
            print(f"    {YELLOW}alerte{RESET} {alert[:300]}")

    # 2. Comparaison à la référence
    reference = _snapshot(REFERENCES_DIR / project)
    if args.update:
        _write_reference(project, files)
        report["reference"] = "mise à jour"
        print(f"  référence  : {YELLOW}mise à jour{RESET} ({len(files)} fichiers)")
    elif not reference:
        report["reference"] = "absente"
        print(f"  référence  : {YELLOW}absente{RESET} (lancer avec --update pour la créer)")
    else:
        diff = _compare(files, reference)
        report["diff"] = diff
        if not any(diff.values()):
            report["reference"] = "identique"
            print(f"  référence  : {GREEN}identique{RESET}")
        else:
            report["reference"] = "différente"
            print(
                f"  référence  : {RED}différente{RESET} — "
                f"+{len(diff['added'])} ajoutés, −{len(diff['removed'])} retirés, ~{len(diff['changed'])} modifiés"
            )
            for kind, sign in (("added", "+"), ("removed", "−"), ("changed", "~")):
                for rel in diff[kind][:15]:
                    print(f"    {sign} {rel}")
                    if args.diff and kind == "changed":
                        _print_diff(rel, reference[rel], files[rel])

    # 3. TypeScript (mêmes préparations que le pipeline)
    if not args.no_tsc and core and not core.template_failure and not report.get("crash"):
        t1 = time.perf_counter()
        prev_ok, pre_run_error = run_pre_run_commands(core.stack_cfg, str(workdir))
        if pre_run_error or not prev_ok:
            report["tsc"] = {"ok": False, "error": pre_run_error or "commande de préparation échouée"}
            print(f"  tsc        : {RED}préparation échouée{RESET} — {report['tsc']['error'][:200]}")
        else:
            tsc = await run_tsc_check(str(workdir))
            errors = tsc.get("errors") or []
            report["tsc"] = {
                "ok": tsc.get("success") is True,
                "skipped": tsc.get("skip_reason") if tsc.get("skipped") else None,
                "errors_count": len(errors),
                "errors": [
                    f"{e.get('file')}({e.get('line')},{e.get('col')}) {e.get('code')}: {e.get('message')}"
                    for e in errors[:20]
                ],
            }
            elapsed = round(time.perf_counter() - t1, 1)
            if report["tsc"]["ok"]:
                print(f"  tsc        : {GREEN}OK{RESET} ({elapsed}s)")
            elif report["tsc"]["skipped"]:
                print(f"  tsc        : {RED}non exécuté{RESET} ({report['tsc']['skipped']})")
            else:
                print(f"  tsc        : {RED}{len(errors)} erreur(s){RESET} ({elapsed}s)")
                for line in report["tsc"]["errors"][:8]:
                    print(f"    {RED}•{RESET} {line[:300]}")

    if not args.keep:
        shutil.rmtree(workdir, ignore_errors=True)
        try:
            WORK_ROOT.rmdir()  # seulement s'il est vide
        except OSError:
            pass
    else:
        print(f"  dossier    : {workdir}")

    tsc_ok = args.no_tsc or (report.get("tsc") or {}).get("ok", False)
    report["ok"] = (
        not report.get("crash")
        and not report["errors"]
        and report["reference"] in ("identique", "mise à jour")
        and tsc_ok
    )
    return report


async def main() -> int:
    parser = argparse.ArgumentParser(description="Harnais : rejoue les générateurs sur les déclarations étalons")
    parser.add_argument("--only", action="append", default=[], help="Ne rejouer que ce projet (répétable)")
    parser.add_argument("--no-tsc", action="store_true", help="Ne pas lancer la vérification TypeScript")
    parser.add_argument("--update", action="store_true", help="Accepter la génération actuelle comme référence")
    parser.add_argument("--diff", action="store_true", help="Afficher le diff des fichiers modifiés")
    parser.add_argument("--keep", action="store_true", help="Conserver les dossiers générés")
    args = parser.parse_args()

    declarations = sorted(DECLARATIONS_DIR.glob("*.json"))
    if args.only:
        declarations = [d for d in declarations if d.stem in args.only]
    if not declarations:
        print(f"{RED}✗ Aucune déclaration dans {DECLARATIONS_DIR}{RESET} "
              "(les capturer avec scripts/capture_declarations.py)")
        return 1

    print(f"{BOLD}═══ Harnais — {len(declarations)} déclaration(s) ═══{RESET}")
    reports = []
    for decl_path in declarations:
        try:
            reports.append(await _run_one(decl_path, args))
        except Exception as e:
            print(f"  {RED}✗ {decl_path.name} : {e}{RESET}")
            reports.append({"project": decl_path.stem, "ok": False, "crash": str(e)})

    print(f"\n{BOLD}═══ Récapitulatif ═══{RESET}")
    for r in reports:
        icon = f"{GREEN}✓{RESET}" if r["ok"] else f"{RED}✗{RESET}"
        tsc = r.get("tsc") or {}
        tsc_txt = "—" if args.no_tsc or not tsc else ("OK" if tsc.get("ok") else f"{tsc.get('errors_count', '?')} err.")
        gen_txt = "plantée" if r.get("crash") else (f"{len(r.get('errors', []))} err." if r.get("errors") else "OK")
        alerts_txt = f"  ({len(r['alerts'])} alerte(s))" if r.get("alerts") else ""
        print(f"  {icon} {r['project']:<22} génération {gen_txt:<9} référence {r.get('reference', '—'):<11} tsc {tsc_txt}{alerts_txt}")

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    report_path = REPORTS_DIR / f"harness_{stamp}.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump({"created_at": stamp, "args": vars(args), "reports": reports}, f, indent=2, ensure_ascii=False)
    print(f"\n  Rapport : {report_path.relative_to(_ROOT)}")

    return 0 if all(r["ok"] for r in reports) else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
