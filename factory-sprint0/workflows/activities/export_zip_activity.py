"""
workflows/activities/export_zip_activity.py

Exporte le projet généré en ZIP après la fin du pipeline complet (post-FrontendAgent + Learner).
Déplacé hors de dev_test_activity (Sprint 4.9A) : le ZIP doit capturer l'état final incluant
les améliorations UI du FrontendAgent, pas l'état intermédiaire post-build.

Contrat d'entrée :
  project_name  : str
  build_status  : str

Contrat de sortie :
  zip_path      : str  (chemin absolu du zip, ou "" si échec/skip)
  zip_size_kb   : int
"""
from __future__ import annotations

import logging
import os
import zipfile
from typing import Any, Dict

from temporalio import activity

logger = logging.getLogger(__name__)

_EXCLUDE_DIRS = {"node_modules", ".next", ".git", "dist", ".turbo"}
_EXCLUDE_EXTS = {".tsbuildinfo"}
_EXCLUDE_FILES = {"tsconfig.tsbuildinfo"}


@activity.defn(name="export_zip_activity")
async def export_zip_activity(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """Crée un ZIP propre du projet généré (sans node_modules/.next)."""
    project_name: str = input_data.get("project_name", "")
    build_status: str = str(input_data.get("build_status", "BUILD_FAILED"))

    if build_status != "BUILD_SUCCESS" or not project_name:
        return {"zip_path": "", "zip_size_kb": 0}

    factory_workdir = os.getenv("FACTORY_WORKDIR", "/app/generated-projects")
    project_workdir = os.path.join(factory_workdir, project_name)
    exports_dir = os.path.join(factory_workdir, "exports")

    try:
        os.makedirs(exports_dir, exist_ok=True)
        zip_path = os.path.join(exports_dir, f"{project_name}.zip")

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
            for root, dirs, files in os.walk(project_workdir):
                dirs[:] = [d for d in dirs if d not in _EXCLUDE_DIRS]
                for filename in files:
                    if filename in _EXCLUDE_FILES:
                        continue
                    if any(filename.endswith(ext) for ext in _EXCLUDE_EXTS):
                        continue
                    full_path = os.path.join(root, filename)
                    arcname = os.path.relpath(full_path, project_workdir).replace("\\", "/")
                    zf.write(full_path, arcname)

        zip_size_kb = os.path.getsize(zip_path) // 1024
        activity.logger.info(f"[export_zip] ✓ {zip_path} ({zip_size_kb} KB)")
        return {"zip_path": zip_path, "zip_size_kb": zip_size_kb}

    except Exception as e:
        activity.logger.warning(f"[export_zip] non bloquant : {e}")
        return {"zip_path": "", "zip_size_kb": 0}
