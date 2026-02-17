"""Utilitaire de chargement centralisé des prompts."""
import os
from pathlib import Path


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
