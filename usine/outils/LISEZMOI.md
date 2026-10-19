# Outils de travail de l'usine (rangés le 15 oct 2026)

Lancés depuis la racine du projet, avec `$env:PYTHONPATH` = la racine. Docker Desktop doit tourner (base `temporal-postgresql`) ;
il s'arrête à chaque redémarrage du PC.

| Outil | À quoi il sert |
|---|---|
| `lot.ps1 <nom> <apprentissage\|corpus> <brief>…` | un lot de briefs lus par la **session Claude isolée** (boîte aux lettres), puis fabriqués et jugés. Journal : `runs/lots/lot-<nom>.log`. Lancer détaché (`Start-Process`), puis rouvrir la session isolée (`C:\Users\BAMBARA Arthur\lecteur-isole`, message : « Lis le fichier DEMARRAGE.md de ce dossier et suis-le exactement. »). Empêche la mise en veille tant qu'il tourne |
| `refab_claude.py <brief> <dossier …-claude-comprendre>` | refabrique une app depuis une lecture Claude déjà faite (0 $, sans la session) — après une correction de l'usine |
| `comparer_lectures.py <nom>…` | compare la lecture gpt-5.5 et la lecture Claude d'un même brief |
| `bilan_claude.py` | bilan de la mesure Claude face aux critères écrits d'avance (19 briefs connus) |
| `photo.py <sortie> [répétition]` + `comparer.py <avant> <après>` | prouver qu'une restructuration ne change AUCUN résultat produit (règles, écrans, droits, données) |
| `ecrans_seuls.py <run>` | rejoue seulement les tests d'écran d'une app déjà construite (avec les tests actuels du squelette) |
| `nettoyer.py <répétition à garder> <app>… [--vraiment]` | nettoie `runs/` (garde compréhensions, résumés, dernière app de chaque brief) ; essai à blanc sans `--vraiment`. **Suppression : demander l'accord de l'utilisateur** |
| `essai_boite.py` | essai de la boîte aux lettres sans session (répondeur automatique) |
| `racine-deux-auteurs.md` | le recensement « une décision prise à deux endroits » (étape 3, traité : registre n° 48) |

Les commandes de l'usine elle-même : `python -m usine fabriquer|comprendre|demarrer|carte`, `python -m usine.repetition`,
`python -m usine.mesures.corpus`, `python -m usine.tableau` (voir USINE.md §10).
