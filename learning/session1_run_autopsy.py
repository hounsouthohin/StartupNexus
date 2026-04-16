"""
SESSION 1 — Autopsie d'un run réel
====================================
Objectif : comprendre la structure d'un run_report et lire
ce que la factory a produit sans lancer quoi que ce soit.

Lance ce script depuis la racine du projet :
    python learning/session1_run_autopsy.py

Ou pour voir un run précis :
    python learning/session1_run_autopsy.py --run-id 65b64e38
"""

import json
import os
import sys
import argparse
from pathlib import Path
from datetime import datetime

# ── Chemins ──────────────────────────────────────────────────────────────────
REPORTS_DIR = Path(__file__).resolve().parent.parent / "factory-sprint0" / "logs" / "metrics" / "run_reports"


# ── Helpers d'affichage ──────────────────────────────────────────────────────

def _color(text: str, code: str) -> str:
    """Ajoute une couleur ANSI si le terminal la supporte."""
    if sys.stdout.isatty():
        return f"\033[{code}m{text}\033[0m"
    return text

def green(t): return _color(t, "32")
def red(t):   return _color(t, "31")
def yellow(t): return _color(t, "33")
def cyan(t):  return _color(t, "36")
def bold(t):  return _color(t, "1")


def load_report(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def format_duration(seconds: float) -> str:
    if seconds < 60:
        return f"{seconds:.0f}s"
    m = int(seconds) // 60
    s = int(seconds) % 60
    return f"{m}m{s:02d}s"


def status_icon(report: dict) -> str:
    if report.get("build_success"):
        return green("✅ SUCCESS")
    if report.get("build_attempted"):
        return red("❌ BUILD_FAILED")
    return yellow("⛔ NOT_BUILT")


# ── Affichage d'un run en détail ─────────────────────────────────────────────

def print_run_detail(report: dict):
    sep = "─" * 60
    print(f"\n{bold(sep)}")
    print(bold(f"  RUN DETAIL"))
    print(bold(sep))

    # ── Identité ──
    print(f"\n{cyan('● Identité')}")
    print(f"  run_id       : {report.get('run_id', '?')}")
    print(f"  projet       : {report.get('project_name', '?')}")
    print(f"  workflow_id  : {report.get('workflow_id', '?')}")
    ts = report.get("generated_at", "")
    if ts:
        try:
            dt = datetime.fromisoformat(ts)
            ts = dt.strftime("%d/%m/%Y %H:%M:%S UTC")
        except Exception:
            pass
    print(f"  généré le    : {ts}")
    print(f"  durée totale : {format_duration(report.get('duration_seconds', 0))}")

    # ── Résultat final ──
    print(f"\n{cyan('● Résultat final')}")
    icon = status_icon(report)
    print(f"  statut       : {icon}")
    print(f"  build tenté  : {'oui' if report.get('build_attempted') else 'non'}")
    print(f"  tentatives   : {report.get('build_attempts', 0)}")
    print(f"  root_cause   : {report.get('root_cause_category') or '(non identifiée)'}")
    print(f"  message final: {report.get('final_message', '?')}")

    # ── Spec & Requirements ──
    print(f"\n{cyan('● Spec & Requirements')}")
    cov = report.get("spec_coverage", 0)
    cov_str = f"{cov*100:.0f}%" if isinstance(cov, float) else str(cov)
    met = report.get("requirements_met", 0)
    total = report.get("requirements_total", 0)
    unmet = report.get("requirements_unmet_list") or report.get("requirements_unmet") or []
    print(f"  spec_coverage: {cov_str}  ({met}/{total} requirements)")
    if unmet:
        print(f"  non couverts :")
        for item in (unmet if isinstance(unmet, list) else []):
            print(f"    - {item}")

    # ── Fichiers générés ──
    print(f"\n{cyan('● Fichiers générés')}")
    print(f"  total        : {report.get('files_generated', report.get('dev_files_count', '?'))}")

    # ── Vérifications déterministes ──
    print(f"\n{cyan('● Vérifications déterministes (avant build)')}")
    pv = report.get("prisma_validate", {})
    if pv:
        pv_ok = "✅ valide" if pv.get("ok") else "❌ invalide"
        pv_ran = "a tourné" if pv.get("ran") else "skipped"
        print(f"  prisma_validate : {pv_ok}  ({pv_ran})")
    tsc_ok = report.get("tsc_ok")
    tsc_ran = report.get("tsc_ran")
    tsc_errors = report.get("tsc_errors_count", 0)
    if tsc_ran is not None:
        tsc_str = "✅ 0 erreur" if tsc_ok else f"❌ {tsc_errors} erreur(s)"
        print(f"  tsc             : {tsc_str}  ({'a tourné' if tsc_ran else 'skipped'})")

    # ── Erreur build ──
    build_err = report.get("last_build_error") or report.get("error") or ""
    if build_err:
        print(f"\n{cyan('● Erreur de build')}")
        lines = build_err.strip().split("\n")[:6]
        for line in lines:
            print(f"  {red(line)}")
        if len(build_err.split("\n")) > 6:
            print(f"  {yellow('...(tronqué)')}")

    # ── Alertes internes ──
    flags = report.get("contradiction_flags", [])
    if flags:
        print(f"\n{cyan('● Alertes internes (contradiction_flags)')}")
        for flag in flags:
            print(f"  {yellow('⚠')} {flag}")

    print()


# ── Vue tableau de tous les runs ─────────────────────────────────────────────

def print_all_runs(reports: list[dict]):
    print(f"\n{bold('═' * 90)}")
    print(bold(f"  TOUS LES RUNS ({len(reports)} au total) — triés du plus récent au plus ancien"))
    print(bold('═' * 90))
    print(f"  {'DATE':16} {'PROJET':20} {'DURÉE':7} {'STATUT':14} {'COV':5} {'REQ':6} {'BUILD':5} {'ROOT_CAUSE'}")
    print("  " + "─" * 86)

    for r in reports:
        ts = r.get("generated_at", "")
        try:
            dt = datetime.fromisoformat(ts)
            date_str = dt.strftime("%d/%m %H:%M")
        except Exception:
            date_str = ts[:16]

        project  = (r.get("project_name") or "?")[:18]
        duration = format_duration(r.get("duration_seconds", 0))
        icon     = status_icon(r)

        cov = r.get("spec_coverage", 0)
        cov_str = f"{cov*100:.0f}%" if isinstance(cov, float) else "?"

        met   = r.get("requirements_met", 0)
        total = r.get("requirements_total", 0)
        req_str = f"{met}/{total}"

        attempts = r.get("build_attempts", 0)
        root     = (r.get("root_cause_category") or "-")[:20]

        print(f"  {date_str:16} {project:20} {duration:7} {icon:22} {cov_str:5} {req_str:6} {str(attempts):5} {root}")

    print()


# ── Comparaison succès vs échec ──────────────────────────────────────────────

def print_comparison(success: dict, failure: dict):
    print(f"\n{bold('═' * 60)}")
    print(bold("  COMPARAISON : SUCCÈS vs ÉCHEC"))
    print(bold('═' * 60))

    fields = [
        ("Projet",         "project_name"),
        ("Durée",          "duration_seconds"),
        ("Build tenté",    "build_attempted"),
        ("Tentatives",     "build_attempts"),
        ("Spec coverage",  "spec_coverage"),
        ("Req met/total",  None),
        ("Fichiers",       "files_generated"),
        ("TSC ok",         "tsc_ok"),
        ("TSC erreurs",    "tsc_errors_count"),
        ("Root cause",     "root_cause_category"),
    ]

    print(f"\n  {'CHAMP':20} {'SUCCÈS':25} {'ÉCHEC'}")
    print("  " + "─" * 70)

    for label, key in fields:
        if key is None:  # requirements
            s_val = f"{success.get('requirements_met',0)}/{success.get('requirements_total',0)}"
            f_val = f"{failure.get('requirements_met',0)}/{failure.get('requirements_total',0)}"
        elif key == "duration_seconds":
            s_val = format_duration(success.get(key, 0))
            f_val = format_duration(failure.get(key, 0))
        elif key == "spec_coverage":
            sc = success.get(key, 0)
            fc = failure.get(key, 0)
            s_val = f"{sc*100:.0f}%" if isinstance(sc, float) else str(sc)
            f_val = f"{fc*100:.0f}%" if isinstance(fc, float) else str(fc)
        else:
            s_val = str(success.get(key, "?"))
            f_val = str(failure.get(key, "?"))

        print(f"  {label:20} {green(s_val):33} {red(f_val)}")

    print()


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Autopsie d'un run_report")
    parser.add_argument("--run-id", help="Affiche le détail d'un run précis (partiel OK)")
    parser.add_argument("--compare", action="store_true", help="Compare succès vs échec")
    parser.add_argument("--list", action="store_true", help="Tableau de tous les runs (défaut)")
    args = parser.parse_args()

    if not REPORTS_DIR.exists():
        print(red(f"Répertoire introuvable : {REPORTS_DIR}"))
        sys.exit(1)

    # Charger tous les reports
    all_reports = []
    for path in sorted(REPORTS_DIR.glob("run_report_*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        try:
            all_reports.append((path, load_report(path)))
        except Exception as e:
            print(yellow(f"  ⚠ Impossible de lire {path.name}: {e}"))

    if not all_reports:
        print(red("Aucun run_report trouvé."))
        sys.exit(1)

    reports_only = [r for _, r in all_reports]

    # ── Mode : détail d'un run précis
    if args.run_id:
        matched = [(p, r) for p, r in all_reports if args.run_id in r.get("run_id", "")]
        if not matched:
            print(red(f"Aucun run trouvé avec id contenant '{args.run_id}'"))
            sys.exit(1)
        for _, r in matched:
            print_run_detail(r)
        return

    # ── Mode : comparaison succès vs échec
    if args.compare:
        successes = [r for r in reports_only if r.get("build_success")]
        failures  = [r for r in reports_only if not r.get("build_success") and r.get("build_attempted")]
        if not successes:
            print(yellow("Aucun run avec build_success=True trouvé."))
            return
        if not failures:
            print(yellow("Aucun run avec build_attempted=True et build_success=False trouvé."))
            return
        print_comparison(successes[0], failures[0])
        print(bold("=== Détail du SUCCÈS ==="))
        print_run_detail(successes[0])
        print(bold("=== Détail de l'ÉCHEC ==="))
        print_run_detail(failures[0])
        return

    # ── Mode par défaut : tableau + détail du run le plus récent
    print_all_runs(reports_only)

    print(bold("=== Détail du run le plus récent ==="))
    print_run_detail(reports_only[0])

    print(cyan("─" * 60))
    print(cyan("COMMANDES UTILES :"))
    print(f"  python learning/session1_run_autopsy.py                 → tableau + dernier run")
    print(f"  python learning/session1_run_autopsy.py --run-id 65b64e → détail d'un run précis")
    print(f"  python learning/session1_run_autopsy.py --compare        → succès vs échec côte à côte")
    print()


if __name__ == "__main__":
    main()
