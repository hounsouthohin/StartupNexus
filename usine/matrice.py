"""Le calculateur de matrice (usine/calculateur/capability_matrix.py, venu de l'ancienne usine le 13 nov 2026,
au retrait de factory-sprint0). Une seule source : ce module ne fait que le réexporter."""
from .calculateur.capability_matrix import (  # noqa: F401
    VISITOR, AccessDeclaration, Cell, Entity, Matrix, _norm, compute_matrix, derive_nav, explain, questions,
    questions_detail,
)
