"""LE MIROIR (N1.4) : le client voit, avec le concepteur, ce que l'usine a compris ; rien ne se fabrique avant
sa validation. N1.4a : le contenu (contenu.py). À venir : réponses par clics (b), porte (c), page (d),
compléments en texte libre (e).

    python -m usine.miroir runs/<n°>-<nom>-comprendre [...]   → miroir.json + miroir.md, et sa couverture
"""
from .contenu import construire, construire_hors, couverture, depuis_run, ecrire, en_markdown  # noqa: F401
