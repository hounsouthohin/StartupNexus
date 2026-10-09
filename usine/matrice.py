"""Le calculateur de matrice, utilisé EN PLACE (factory-sprint0/agents/capability_matrix.py).
Il ne déménagera qu'au retrait de l'ancienne usine (USINE.md §8) : une seule source."""
import sys
from pathlib import Path

_FACTORY = Path(__file__).resolve().parents[1] / "factory-sprint0"
if str(_FACTORY) not in sys.path:
    sys.path.insert(0, str(_FACTORY))

from agents.capability_matrix import (  # noqa: E402,F401
    VISITOR, AccessDeclaration, Cell, Entity, Matrix, _norm, compute_matrix, derive_nav, explain, questions,
)
