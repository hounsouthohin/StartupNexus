# Étape 3 — « une décision prise à plusieurs endroits » : recensement (lecture seule, 12 oct)

Règle visée : un fait, un seul auteur (la matrice pour les droits ; `traduire/modele.py` pour la forme de l'app).
Les juges recalculent EXPRÈS depuis la matrice (principe « le juge = la source ») : ce n'est pas un doublon.

| # | Décision | Auteurs aujourd'hui | Risque | Remède proposé |
|---|---|---|---|---|
| A | « le lien vers le profil du propriétaire est posé automatiquement » | `modele.py` (profil + collection + même propriétaire), `capability_matrix.py` §4 (profil + même propriétaire + **créateur = propriétaire**), `cas.mts` (copie de modele.py) | conditions DIFFÉRENTES : latent tant que la saisie pour autrui est refusée ; explose le jour où elle est construite | une seule définition, dans la matrice (`auto_links` existe déjà) ; modele.py et cas.mts la lisent |
| B | droits des lignes (enfants) dans le calculateur | §2 (ancien héritage : voir, créer, modifier) ET §3b (nouveau : tout, par action) | §2 est devenu du code mort qui peut contredire §3b | supprimer la partie enfants du §2 (banc des 14 matrices pour le prouver) |
| C | « on ajoute une ligne dans les états où elle se modifie » | `schema.py`, `ecran.py` (creer_pendant), `e2e/blocs/enfants.ts`, `verification/blocs/enfant.mts` — 4 endroits qui recodent la même règle | une modification oubliée dans l'un des 4 = n° 46 bis | la matrice porte `create_while` sur la case ; les 4 la lisent |
| D | « ne voit pas les siens » (choisir parmi ses fiches) | calculateur §4 (`personnes_de`) et `repetition.variante` (réécrit la même logique) | outillage : une variante fausse fausserait la mesure | variante appelle la fonction du calculateur |
| E | les motifs de refus d'un bloc pas construit | `description.py` (texte du refus), `blocs/__init__.py` (repère texte), `repetition.py` (REFUS_BLOCS + déclencheurs de variante) — couplés par des **morceaux de phrase** | un message reformulé casse la mesure en silence (vu le 10 oct : « enfants ») | un code de refus stable (`bloc:nature:child`…) dans le message ; les 3 lisent le code |

Ordre proposé : B (nul en risque), A, C, E, D. Chaque remède : banc des matrices + vérification à sec + refabrication.
