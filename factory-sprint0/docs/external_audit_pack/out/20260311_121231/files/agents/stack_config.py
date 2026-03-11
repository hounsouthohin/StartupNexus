"""
Stack-as-Config loader — Sprint 3 Phase C.

Charge la configuration stack depuis config/stacks/<stack_id>.json.
Fournit un cache module-level et des fallbacks vides si le fichier est absent.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from jsonschema import ValidationError, validate

logger = logging.getLogger(__name__)

_STACK_CACHE: dict[str, dict] = {}
_DEFAULT_STACK_ID = "nextjs-clerk-prisma"
_CONFIG_BASE = Path(__file__).parent.parent / "config" / "stacks"
_SCHEMA_PATH = Path(__file__).parent.parent / "schemas" / "stack_config.schema.json"


class StackConfigError(Exception):
    """Erreur de configuration stack invalide ou incomplète."""


def _load_stack_schema() -> dict:
    if not _SCHEMA_PATH.exists():
        raise StackConfigError(f"[stack_config] Schéma introuvable: {_SCHEMA_PATH}")
    try:
        with open(_SCHEMA_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        raise StackConfigError(f"[stack_config] Impossible de charger le schéma: {e}") from e


def load_stack_config(stack_id: str = _DEFAULT_STACK_ID) -> dict:
    """
    Charge et met en cache la configuration stack depuis config/stacks/<stack_id>.json.
    Lève StackConfigError si le fichier est absent/invalide (fail-fast).
    """
    if stack_id in _STACK_CACHE:
        return _STACK_CACHE[stack_id]

    config_path = _CONFIG_BASE / f"{stack_id}.json"
    schema = _load_stack_schema()
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        validate(instance=config, schema=schema)
        _STACK_CACHE[stack_id] = config
        logger.info(f"[stack_config] Config chargée: {stack_id} ({len(config)} clés)")
        return config
    except FileNotFoundError:
        raise StackConfigError(f"[stack_config] Config introuvable: {config_path}") from None
    except ValidationError as e:
        raise StackConfigError(
            f"[stack_config] Stack '{stack_id}' invalide: {e.message}"
        ) from e
    except Exception as e:
        raise StackConfigError(f"[stack_config] Échec chargement {stack_id}: {e}") from e


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


def get_root_file(stack_id: str = _DEFAULT_STACK_ID) -> str:
    """
    Retourne le fichier racine qui identifie le répertoire projet.
    Ex: 'package.json' pour Node/Next.js, 'pyproject.toml' pour Python.
    Utilisé par _find_project_dir pour déduire le workdir du projet généré.
    Fallback: 'package.json' (stack Node par défaut).
    """
    return load_stack_config(stack_id).get("root_file", "package.json")


def get_commands(stack_id: str = _DEFAULT_STACK_ID) -> dict[str, str]:
    """
    Retourne les commandes d'exécution de la stack (install, build, test, etc.).
    Ex: {"install_legacy": "npm install --legacy-peer-deps", "build": "npm run build"}
    Résout Config-Runtime Drift : commands déclaré dans JSON mais jamais consommé.
    """
    return load_stack_config(stack_id).get("commands", {})


def get_qdrant_filter_cfg(stack_id: str = _DEFAULT_STACK_ID) -> dict:
    """
    Retourne la config qdrant_filter (collection + filter) pour la stack.
    Résout Config-Runtime Drift : qdrant_filter déclaré dans JSON mais jamais consommé.
    """
    return load_stack_config(stack_id).get("qdrant_filter", {})


def get_cleanup_artifacts(stack_id: str = _DEFAULT_STACK_ID) -> list[str]:
    """
    Répertoires à supprimer après build (build artifacts, dépendances lourdes).
    Node.js: ['.next', 'node_modules'] | Python: ['__pycache__', '.venv']
    Fallback: liste Node.js pour compatibilité backward.
    """
    return load_stack_config(stack_id).get("cleanup_artifacts", [".next", "node_modules"])


def get_forbidden_paths(stack_id: str = _DEFAULT_STACK_ID) -> list[str]:
    """Retourne les chemins de répertoires interdits (ex: pages/, src/pages/)."""
    return load_stack_config(stack_id).get("forbidden_paths", ["pages/", "src/pages/"])


def get_workdir_keep_extra(stack_id: str = _DEFAULT_STACK_ID) -> list[str]:
    """
    Répertoires supplémentaires à préserver entre les runs (cache, dépendances).
    Fusionné avec les répertoires système (_WORKDIR_KEEP) dans dev.py.
    """
    return load_stack_config(stack_id).get("workdir_keep_extra", ["node_modules", ".npm"])
