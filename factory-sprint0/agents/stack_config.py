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


def get_llm_models(stack_id: str = _DEFAULT_STACK_ID) -> dict[str, str]:
    """
    Retourne les modèles LLM configurés par rôle pour cette stack.
    Clés : architect_base, architect_planner, reviewer, dev (fallback: OPENAI_MODEL env var).
    """
    return load_stack_config(stack_id).get("llm_models", {})

