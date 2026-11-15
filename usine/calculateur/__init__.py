"""Le CALCULATEUR de la matrice des droits (capability_matrix.py) et son banc d'essai (banc.py) : chaque
matrices/<projet>.access.yaml est calculé puis comparé case par case à matrices/<projet>.expected.yaml, écrite
AVANT le calcul ; declarations/<projet>.json ne sert qu'à fournir le texte du brief (citations vérifiées).

    python -m usine.calculateur.banc [--summary] [--only <projet>]
"""
