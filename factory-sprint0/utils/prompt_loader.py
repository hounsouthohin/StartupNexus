"""Utilitaire de chargement centralisé des prompts."""
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


def load_prompt(prompt_name: str) -> str:
    """
    Charge un prompt depuis prompts/{prompt_name}.md

    Args:
        prompt_name: Nom du fichier sans extension (ex: "dev", "architect")

    Returns:
        Contenu du prompt

    Raises:
        FileNotFoundError: Si le fichier n'existe pas
    """
    project_root = Path(__file__).parent.parent
    prompt_path = project_root / "prompts" / f"{prompt_name}.md"

    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt introuvable: {prompt_path}")

    return prompt_path.read_text(encoding="utf-8")


def load_stack_prompt(agent_name: str, stack_id: str) -> str:
    """
    Assemble le prompt final: prompts/base/<agent>.md + prompts/stacks/<stack>/rules_<agent>.md.
    Compatibilité: fallback vers prompts/<agent>.md si base introuvable.
    """
    project_root = Path(__file__).parent.parent
    base_path = project_root / "prompts" / "base" / f"{agent_name}.md"
    legacy_path = project_root / "prompts" / f"{agent_name}.md"

    if base_path.exists():
        base_prompt = base_path.read_text(encoding="utf-8")
    elif legacy_path.exists():
        logger.warning(
            f"[prompt_loader] base/{agent_name}.md introuvable; fallback legacy prompts/{agent_name}.md"
        )
        base_prompt = legacy_path.read_text(encoding="utf-8")
    else:
        raise FileNotFoundError(
            f"Prompt de base introuvable pour '{agent_name}': {base_path} / {legacy_path}"
        )

    rules_path = (
        project_root
        / "prompts"
        / "stacks"
        / stack_id
        / f"rules_{agent_name}.md"
    )
    if not rules_path.exists():
        logger.warning(
            f"[prompt_loader] Rules stack introuvables pour {stack_id}: {rules_path.name}"
        )
        return base_prompt

    stack_rules = rules_path.read_text(encoding="utf-8")
    return f"{base_prompt}\n\n---\n\n{stack_rules}"


def load_base_prompt(agent_name: str) -> str:
    """
    Charge explicitement prompts/base/<agent>.md.
    N'utilise pas de fallback legacy pour éviter toute ambiguïté.
    """
    project_root = Path(__file__).parent.parent
    base_path = project_root / "prompts" / "base" / f"{agent_name}.md"
    if not base_path.exists():
        raise FileNotFoundError(f"Base prompt introuvable: {base_path}")
    return base_path.read_text(encoding="utf-8")


def load_stack_rules_only(agent_name: str, stack_id: str) -> str:
    """
    Charge uniquement prompts/stacks/<stack_id>/rules_<agent>.md.
    """
    project_root = Path(__file__).parent.parent
    rules_path = (
        project_root / "prompts" / "stacks" / stack_id / f"rules_{agent_name}.md"
    )
    if not rules_path.exists():
        logger.warning(f"[prompt_loader] Rules stack absentes: {rules_path}")
        return ""
    return rules_path.read_text(encoding="utf-8")
