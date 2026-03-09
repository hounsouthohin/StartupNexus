"""
agents/spec_coverage.py
Calcul déterministe de la couverture spec (requirements vs fichiers générés).

T003 — Délègue à requirements_engine (source de vérité unique, T002).
Plus de logique dupliquée ni de matching permissif divergent.
"""

from .requirements_engine import compute_coverage as _engine_compute_coverage


def compute_spec_coverage(requirements: list, combined_files: dict) -> dict:
    """
    Compare requirements[] (Architect) vs combined_files (DevAgent).
    Retourne spec_coverage en pourcentage + liste des requirements non couverts.
    Algorithme déterministe — aucun LLM.

    Délègue à requirements_engine.compute_coverage (T002/T003).
    """
    return _engine_compute_coverage(requirements, combined_files)
