"""
Stack-as-Config loader — Sprint 3 Phase C.

Charge la configuration stack depuis config/stacks/<stack_id>.json.
Fournit un cache module-level et des fallbacks vides si le fichier est absent.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

_STACK_CACHE: dict[str, dict] = {}
_DEFAULT_STACK_ID = "nextjs-clerk-prisma"
_CONFIG_BASE = Path(__file__).parent.parent / "config" / "stacks"


def load_stack_config(stack_id: str = _DEFAULT_STACK_ID) -> dict:
    """
    Charge et met en cache la configuration stack depuis config/stacks/<stack_id>.json.
    Retourne un dict vide si le fichier est absent ou illisible (jamais d'exception levée).
    """
    if stack_id in _STACK_CACHE:
        return _STACK_CACHE[stack_id]

    config_path = _CONFIG_BASE / f"{stack_id}.json"
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        _STACK_CACHE[stack_id] = config
        logger.info(f"[stack_config] Config chargée: {stack_id} ({len(config)} clés)")
        return config
    except FileNotFoundError:
        logger.warning(f"[stack_config] Config introuvable: {config_path} — fallback hardcodé actif")
        _STACK_CACHE[stack_id] = {}
        return {}
    except Exception as e:
        logger.error(f"[stack_config] Échec chargement {stack_id}: {e}")
        _STACK_CACHE[stack_id] = {}
        return {}


def get_version_pins(stack_id: str = _DEFAULT_STACK_ID) -> dict[str, str]:
    """Retourne les version pins (ex: next@14.2.25, typescript@^5.3.3)."""
    return load_stack_config(stack_id).get("version_pins", {})


def get_dev_packages(stack_id: str = _DEFAULT_STACK_ID) -> dict[str, str]:
    """Retourne les devDependencies requises (ex: ts-jest@29.1.2)."""
    return load_stack_config(stack_id).get("dev_packages", {})


def get_import_remaps(stack_id: str = _DEFAULT_STACK_ID) -> dict[str, dict[str, str]]:
    """Retourne les remappings d'imports (package_fixes, source_fixes, test_fixes, router_fixes)."""
    return load_stack_config(stack_id).get("import_remaps", {})


def get_peer_dependency_minimums(stack_id: str = _DEFAULT_STACK_ID) -> dict[str, str]:
    """Retourne les versions minimum des peer dependencies (ex: react@^18.2.0)."""
    return load_stack_config(stack_id).get("peer_dependency_minimums", {})


def get_forbidden_imports(stack_id: str = _DEFAULT_STACK_ID) -> list[str]:
    """Retourne la liste des imports interdits (bcrypt, jsonwebtoken, etc.)."""
    return load_stack_config(stack_id).get("forbidden_imports", [])


def get_blueprint(stack_id: str = _DEFAULT_STACK_ID) -> dict:
    """Retourne le blueprint (required_files, optional_files)."""
    return load_stack_config(stack_id).get("blueprint", {})


def get_compatibility_matrix(stack_id: str = _DEFAULT_STACK_ID) -> dict:
    """Retourne la matrice de compatibilité (ts-jest@29 requis, jest@30 interdit, etc.)."""
    return load_stack_config(stack_id).get("compatibility_matrix", {})
