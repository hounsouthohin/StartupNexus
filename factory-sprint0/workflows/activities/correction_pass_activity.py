"""
workflows/activities/correction_pass_activity.py
─────────────────────────────────────────────────
Temporal Activity — Correction chirurgicale post-review.

Reçoit les targeted_fixes produits par review_activity (verdict DEGRADED ou INCOHERENT).
Pour chaque fix : remplace fix_code sur disque dans le project workdir.
Relance le build. Retourne le nouveau build_status + les fichiers mis à jour.

Contrainte : exécuté au maximum 1 fois par run (circuit breaker géré dans le workflow).
"""
from __future__ import annotations

import os
import pathlib
import subprocess
import sys
from typing import Any, Dict, List

from temporalio import activity
from temporalio.exceptions import ApplicationError

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

_SUBPROCESS_TIMEOUT = 300


# ── Écriture chirurgicale des fixes sur disque ────────────────────────────────

def _apply_targeted_fixes(
    targeted_fixes: List[Dict[str, str]],
    project_workdir: str,
) -> List[str]:
    """
    Applique les targeted_fixes sur le disque.
    Chaque fix = {file, current_code, fix_code, reason}.
    Retourne la liste des fichiers effectivement modifiés.
    """
    modified: List[str] = []
    base = pathlib.Path(project_workdir)

    for fix in targeted_fixes:
        rel_path = (fix.get("file") or "").strip()
        current_code = fix.get("current_code", "")
        fix_code = fix.get("fix_code", "")
        reason = fix.get("reason", "")

        if not rel_path or not fix_code:
            activity.logger.warning(f"[correction_pass] Fix ignoré — file ou fix_code absent: {fix}")
            continue

        # Guard path traversal
        try:
            target = (base / rel_path).resolve()
            if not str(target).startswith(str(base.resolve())):
                activity.logger.warning(f"[correction_pass] Path traversal détecté — ignoré: {rel_path}")
                continue
        except Exception as e:
            activity.logger.warning(f"[correction_pass] Chemin invalide {rel_path}: {e}")
            continue

        if not target.exists():
            activity.logger.warning(f"[correction_pass] Fichier introuvable sur disque: {target}")
            continue

        try:
            original_content = target.read_text(encoding="utf-8")
        except Exception as e:
            activity.logger.warning(f"[correction_pass] Lecture impossible {rel_path}: {e}")
            continue

        # Remplacement du bloc current_code → fix_code
        if current_code and current_code.strip() in original_content:
            new_content = original_content.replace(current_code.strip(), fix_code.strip(), 1)
        else:
            # Si current_code introuvable, on écrase le fichier complet avec fix_code
            # (dernier recours — le reviewer a produit fix_code comme bloc complet)
            activity.logger.warning(
                f"[correction_pass] current_code introuvable dans {rel_path} — "
                "remplacement fichier complet"
            )
            new_content = fix_code

        try:
            target.write_text(new_content, encoding="utf-8")
            modified.append(rel_path)
            activity.logger.info(
                f"[correction_pass] ✓ {rel_path} corrigé — {reason[:80]}"
            )
        except Exception as e:
            activity.logger.error(f"[correction_pass] Écriture échouée {rel_path}: {e}")

    return modified


# ── Re-build ──────────────────────────────────────────────────────────────────

def _rebuild(project_workdir: str, stack_id: str) -> str:
    """
    Relance npm install + npm run build. Retourne "BUILD_SUCCESS" ou "BUILD_FAILED: ...".
    """
    try:
        from agents.stack_config import get_commands
        cmds = get_commands(stack_id)
        install_cmd = cmds.get("install_legacy", "npm install --legacy-peer-deps").split()
        build_cmd = cmds.get("build", "npm run build").split()
    except Exception:
        install_cmd = ["npm", "install", "--legacy-peer-deps"]
        build_cmd = ["npm", "run", "build"]

    env = os.environ.copy()
    env["NODE_ENV"] = "production"
    env["NEXT_TELEMETRY_DISABLED"] = "1"

    package_json = os.path.join(project_workdir, "package.json")
    if not os.path.isfile(package_json):
        return "BUILD_FAILED: package.json introuvable dans project_workdir"

    activity.logger.info(f"[correction_pass] Re-build dans {project_workdir}")

    for cmd in (install_cmd, build_cmd):
        try:
            result = subprocess.run(
                cmd,
                cwd=project_workdir,
                capture_output=True,
                text=True,
                timeout=_SUBPROCESS_TIMEOUT,
                env=env,
            )
            if result.returncode != 0:
                stderr = (result.stdout + result.stderr).strip()
                label = "install" if cmd is install_cmd else "build"
                return f"BUILD_FAILED: {label} exit {result.returncode}\n{stderr[:2000]}"
        except subprocess.TimeoutExpired:
            return f"BUILD_FAILED: timeout ({_SUBPROCESS_TIMEOUT}s)"
        except Exception as e:
            return f"BUILD_FAILED: exception subprocess — {e}"

    return "BUILD_SUCCESS"


# ── Rescan workdir ────────────────────────────────────────────────────────────

def _scan_workdir(project_workdir: str) -> Dict[str, str]:
    files: Dict[str, str] = {}
    EXTENSIONS = {".ts", ".tsx", ".js", ".jsx", ".json", ".prisma", ".css", ".md"}
    NAMED_FILES = {".env.local", ".env", ".gitignore"}
    IGNORE_DIRS = {"node_modules", ".next", ".git", "dist", "build", ".turbo"}
    base = pathlib.Path(project_workdir)
    for root, dirs, filenames in os.walk(base):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        for filename in filenames:
            _, ext = os.path.splitext(filename)
            if ext in EXTENSIONS or filename in NAMED_FILES:
                abs_path = pathlib.Path(root) / filename
                rel = abs_path.relative_to(base).as_posix()
                try:
                    files[rel] = abs_path.read_text(encoding="utf-8", errors="replace")
                except Exception:
                    pass
    return files


# ── Temporal Activity ─────────────────────────────────────────────────────────

@activity.defn(name="correction_pass_activity")
async def correction_pass_activity(
    input_data: Dict[str, Any],
    run_id: str = "",
) -> Dict[str, Any]:
    """
    Correction chirurgicale post-review.

    Input attendu :
        project_name    : str
        stack_id        : str
        targeted_fixes  : list[dict]  — depuis ReviewReport
        review_verdict  : str         — "DEGRADED" | "INCOHERENT"

    Output :
        correction_applied  : bool
        files_modified      : list[str]
        new_build_status    : str   ("BUILD_SUCCESS" | "BUILD_FAILED: ...")
        updated_files       : dict[str, str]
    """
    project_name = input_data.get("project_name", "projet-sans-nom")
    stack_id = str(input_data.get("stack_id", "nextjs-clerk-prisma"))
    targeted_fixes: List[Dict[str, str]] = input_data.get("targeted_fixes", []) or []
    review_verdict = str(input_data.get("review_verdict", "DEGRADED"))

    factory_workdir = os.getenv("FACTORY_WORKDIR", "/app/generated-projects")
    project_workdir = os.path.join(factory_workdir, project_name)

    activity.logger.info(
        f"[correction_pass] Démarrage — projet={project_name} "
        f"verdict={review_verdict} fixes={len(targeted_fixes)}"
    )

    if not targeted_fixes:
        activity.logger.warning("[correction_pass] Aucun targeted_fix fourni — rien à corriger")
        return {
            "correction_applied": False,
            "files_modified": [],
            "new_build_status": "BUILD_SUCCESS",
            "updated_files": {},
        }

    if not os.path.isdir(project_workdir):
        raise ApplicationError(
            "CORRECTION_WORKDIR_MISSING",
            f"Project workdir introuvable: {project_workdir}",
        )

    # 1. Application des fixes sur disque
    files_modified = _apply_targeted_fixes(targeted_fixes, project_workdir)

    if not files_modified:
        activity.logger.warning("[correction_pass] Aucun fichier modifié — fixes non appliqués")
        return {
            "correction_applied": False,
            "files_modified": [],
            "new_build_status": "BUILD_SUCCESS",
            "updated_files": {},
        }

    # 2. Re-build
    new_build_status = _rebuild(project_workdir, stack_id)
    activity.logger.info(f"[correction_pass] Re-build → {new_build_status[:80]}")

    # 3. Rescan fichiers
    updated_files = _scan_workdir(project_workdir) if new_build_status == "BUILD_SUCCESS" else {}

    return {
        "correction_applied": True,
        "files_modified": files_modified,
        "new_build_status": new_build_status,
        "updated_files": updated_files,
    }
