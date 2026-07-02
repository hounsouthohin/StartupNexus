from __future__ import annotations

import logging
import os
import shutil


logger = logging.getLogger(__name__)


_WORKDIR_KEEP_SYSTEM = {"logs", "config", "snapshots", "__pycache__", ".git"}


def clean_project_workdir(workdir: str, extra_keep: set[str] | None = None) -> None:
    keep = _WORKDIR_KEEP_SYSTEM | (extra_keep or set())
    if not workdir or not os.path.isdir(workdir):
        return
    try:
        for item in os.listdir(workdir):
            if item in keep:
                continue
            full = os.path.join(workdir, item)
            try:
                if os.path.isfile(full) or os.path.islink(full):
                    os.remove(full)
                    logger.info(f"[pre-run cleanup] Fichier supprimé : {item}")
                elif os.path.isdir(full):
                    shutil.rmtree(full, ignore_errors=True)
                    logger.info(f"[pre-run cleanup] Répertoire supprimé : {item}")
            except Exception as item_err:
                logger.warning(f"[pre-run cleanup] Impossible de supprimer {item}: {item_err}")
    except Exception as e:
        logger.warning(f"[pre-run cleanup] Erreur listage workdir '{workdir}': {e}")


def _evaluate_template_condition(condition: str, spec: dict) -> bool:
    """Évalue si un template conditionnel doit être écrit selon les données de la spec."""
    if condition == "has_webhook_routes":
        return any(
            "webhook" in (r.get("path") or "").lower()
            or "stripe" in (r.get("path") or "").lower()
            for r in (spec.get("routes") or [])
        )
    logger.warning("[templates] Condition '%s' inconnue — template écrit par défaut", condition)
    return True


def write_template_files(
    workdir: str,
    stack_cfg: dict,
    project_name: str,
    stack_id: str,
    spec: dict | None = None,
) -> dict:
    import pathlib

    templated = stack_cfg.get("templated_files", {})
    conditional = stack_cfg.get("conditional_templates", {})
    spec_dict = spec or {}

    if not templated or not workdir:
        return {}

    base_dir = pathlib.Path(__file__).parent.parent.parent.parent / "config" / "stacks" / stack_id

    written = {}
    for dest_filename, template_rel_path in templated.items():
        # F-09: évalue la condition avant d'écrire si ce template est conditionnel
        if dest_filename in conditional:
            condition = conditional[dest_filename].get("condition", "")
            if not _evaluate_template_condition(condition, spec_dict):
                logger.info(
                    "[templates] %s ignoré — condition '%s' non remplie par la spec",
                    dest_filename, condition,
                )
                continue

        try:
            template_path = base_dir / template_rel_path
            if not template_path.exists():
                logger.warning(f"[templates] Template introuvable: {template_path}")
                continue
            content = template_path.read_text(encoding="utf-8")
            content = content.replace("{project_name}", project_name)
            # Injecte la route principale depuis le spec.
            # Priorité : /dashboard (hub post-auth) → première page list AUTH-REQUIRED → "/"
            # Note : on filtre sur auth_required pour éviter /blog (liste publique) comme cible post-login.
            _pages = spec_dict.get("pages", []) or []
            _dashboard_page = next(
                (p for p in _pages if isinstance(p, dict) and p.get("path") == "/dashboard"),
                None,
            )
            _list_page = next(
                (p for p in _pages if isinstance(p, dict) and p.get("page_type") == "list" and p.get("auth_required")),
                None,
            )
            _main_route = (
                (_dashboard_page or {}).get("path")
                or (_list_page or {}).get("path")
                or "/"
            )
            content = content.replace("{main_route}", _main_route)
            dest_path = pathlib.Path(workdir) / dest_filename
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            dest_path.write_text(content, encoding="utf-8")
            written[dest_filename] = content
            logger.info(f"[templates] ✓ {dest_filename} écrit depuis template")
        except Exception as e:
            logger.warning(f"[templates] Erreur écriture {dest_filename}: {e}")
    return written
