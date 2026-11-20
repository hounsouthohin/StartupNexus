# Le stylo

> Qui modifie, en ce moment, le code ou les dossiers (`conception/`, `USINE.md`, `AGENTS.md`, `usine/`…), et sur quels
> fichiers. **C'est une coordination visible, pas une garantie d'exclusion** : deux agents peuvent lire la ligne vide en
> même temps. En cas de doute, Arthur arbitre.
>
> - **Prendre** : vérifier que la ligne « En ce moment » dit « libre », puis y écrire : qui, sur quels fichiers, depuis
>   quand, pour quel fil.
> - **Avant d'écrire un fichier** : regarder `git status` et la date de modification du fichier.
> - **Rendre** : remettre « libre », et ajouter une ligne à l'historique.
> - **Une session interrompue** : le stylo reste pris. C'est Arthur qui le libère.
> - Écrire dans un fil de `dialogue/` ne demande pas le stylo, seulement sa propre section.

## En ce moment

*(Depuis le 20 nov : deux périmètres **séparés**, tenus en même temps, pour le contrat des noms à l'écran. Fil
[Codex, auteur du juge du contrat](2026-11-20-juge-du-contrat-par-codex.md).)*

- **Claude Code** (le côté usine), depuis le 19 nov 2026 : `usine/` (description, comprendre, miroir, traduire, la porte),
  `usine/modele-app/`, `usine/exemples/`, `conception/contrat-noms-ecran.md`, et
  `C:\Users\BAMBARA Arthur\essais\contrat-noms\` **sauf** le sous-dossier `juge\` et l'inventaire.
- **Codex** (le côté juge) : **libre**, pour `C:\Users\BAMBARA Arthur\essais\contrat-noms\juge\` et l'inventaire
  (`inventaire.py`, `inventaire.md`, `inventaire-*.json`).

Aucun des deux n'écrit dans le périmètre de l'autre ; un besoin chez l'autre s'écrit dans le fil.

## Historique

| Qui | Fichiers | Pris | Rendu | Fil |
|---|---|---|---|---|
| Claude Code | `USINE.md` §5 (inconnue n° 17, hypothèse : la vision d'Arthur) | 20 nov 2026 15 h 30 | 20 nov 2026 15 h 30 | juge du contrat (message de Codex de 15 h 25) |
| Claude Code | *Écart, signalé ici :* `USINE.md` §7 (registre n° 61 à 63) modifié vers 12 h sans que `USINE.md` soit dans mon périmètre de stylo | 20 nov 2026 ≈ 12 h | 20 nov 2026 ≈ 12 h | contrat des noms à l'écran |
| Claude Code | `dialogue/LISEZMOI.md` (règle 15 complétée : relire après chaque écriture, décidé par Arthur) | 20 nov 2026 12 h 12 | 20 nov 2026 12 h 14 | juge du contrat ; décision d'Arthur |
| Claude Code | `dialogue/LISEZMOI.md` (règle 15, décidée par Arthur), `dialogue/MODELE-FIL.md`, l'en-tête du fil du juge. *Ma ligne « En ce moment » de 12 h 07 a été effacée par une écriture simultanée de ce fichier ; inscrite ici à la place* | 20 nov 2026 12 h 07 | 20 nov 2026 12 h 11 | juge du contrat ; décision d'Arthur |
| Codex (OpenAI) | `juge/inspecteur-actions-v8.mjs`, `juge/inspecteur-voir-v3.mjs`, `juge/preuve-qualification-v7.mjs`, rapports v7 | 20 nov 2026 12 h 01 | 20 nov 2026 12 h 07 | juge du contrat, états et noms |
| Codex (OpenAI) | `juge/lecture-description-v2.mjs`, `juge/inspecteur-actions-v5 à v7.mjs`, `juge/preuve-qualification-v3 à v6.mjs`, rapports v6 | 20 nov 2026 11 h 51 | 20 nov 2026 12 h 01 | juge du contrat, choix et données |
| Codex (OpenAI) | `juge/inspecteur-actions-v4.mjs`, `juge/inspecteur-voir-v2.mjs`, `juge/preuve-qualification-v2.mjs`, leurs rapports | 20 nov 2026 10 h 59 | 20 nov 2026 11 h 51 | juge du contrat, sabotages communs |
| Codex (OpenAI) | `juge/preuve-qualification-v1.mjs`, `juge/rapport-qualification-*-v1.json` | 20 nov 2026 10 h 56 | 20 nov 2026 10 h 58 | juge du contrat, version commune |
| Codex (OpenAI) | `juge/inspecteur-voir.mjs`, `juge/preuve-tout-integre.mjs`, `juge/rapport-tout-integre.json` | 20 nov 2026 10 h 50 | 20 nov 2026 10 h 54 | juge du contrat, lecture et actions |
| Codex (OpenAI) | `juge/inspecteur-actions-v3.mjs`, `juge/preuve-mauvais-lien.mjs`, `juge/preuve-actions-v5.mjs`, leurs rapports | 20 nov 2026 10 h 47 | 20 nov 2026 10 h 50 | juge du contrat, mauvais lien |
| Codex (OpenAI) | `juge/preuve-actions-v4.mjs`, `juge/rapport-actions-v4.json` | 20 nov 2026 10 h 44 | 20 nov 2026 10 h 47 | juge du contrat, titres identiques |
| Codex (OpenAI) | `juge/inspecteur-actions-v2.mjs`, `juge/preuve-actions-v2.mjs`, `juge/preuve-actions-v3.mjs`, leurs rapports | 20 nov 2026 10 h 41 | 20 nov 2026 10 h 44 | juge du contrat, bonne ligne |
| Codex (OpenAI) | `juge/inspecteur-actions.mjs`, `juge/preuve-actions-module.mjs`, `juge/rapport-actions-module.json` | 20 nov 2026 10 h 37 | 20 nov 2026 10 h 40 | juge du contrat, inspecteur séparé |
| Codex (OpenAI) | `juge/preuve-actions-description.mjs`, `juge/rapport-actions-description.json` | 20 nov 2026 10 h 35 | 20 nov 2026 10 h 36 | juge du contrat, noms d'actions |
| Codex (OpenAI) | `juge/preuve-actions.mjs`, `juge/rapport-actions.json` | 20 nov 2026 10 h 31 | 20 nov 2026 10 h 34 | juge du contrat, actions |
| Codex (OpenAI) | `juge/preuve-integree.mjs`, `juge/rapport-integre*.json` | 20 nov 2026 10 h 28 | 20 nov 2026 10 h 31 | juge du contrat, raccordement |
| Codex (OpenAI) | `juge/preuve-ralentie.mjs`, `juge/rapport-ralenti.json` | 20 nov 2026 10 h 16 | 20 nov 2026 10 h 27 | juge du contrat, ralenti |
| Codex (OpenAI) | `juge/attendre-zone.mjs`, `juge/preuve-attente.mjs`, `juge/rapport-attente.json` | 20 nov 2026 10 h 14 | 20 nov 2026 10 h 16 | juge du contrat, attente |
| Codex (OpenAI) | `juge/tranche-sabotages.mjs`, `juge/rapport-sabotages.json` | 20 nov 2026 10 h 13 | 20 nov 2026 10 h 14 | juge du contrat, sabotages |
| Codex (OpenAI) | `juge/moteur-inventaire.mjs`, `juge/preuve-inventaire.mjs`, `juge/rapport-inventaire.json` | 20 nov 2026 10 h 11 | 20 nov 2026 10 h 12 | juge du contrat, inventaire |
| Codex (OpenAI) | `juge/lecture-description.mjs`, `juge/preuve-description.mjs`, `juge/rapport-description.json` | 20 nov 2026 10 h 09 | 20 nov 2026 10 h 10 | juge du contrat, description |
| Codex (OpenAI) | `juge/tranche-jumeaux.mjs`, `juge/rapport-jumeaux*.json` | 20 nov 2026 10 h 06 | 20 nov 2026 10 h 08 | juge du contrat, jumeaux |
| Codex (OpenAI) | `juge/tranche-navigation.mjs`, `juge/rapport-navigation.json` | 20 nov 2026 10 h 04 | 20 nov 2026 10 h 05 | juge du contrat, navigation |
| Codex (OpenAI) | `C:\Users\BAMBARA Arthur\essais\contrat-noms\juge\` ; inventaire réservé mais non modifié | 20 nov 2026 09 h 52 | 20 nov 2026 09 h 59 | [juge du contrat par Codex](2026-11-20-juge-du-contrat-par-codex.md) |
| Claude Code | `USINE.md`, `AGENTS.md`, `conception-technique.md`, `conception/contrat-noms-ecran.md` (renommage), `conception/essai-juge-ecrans.md`, `conception/carte-de-l-usine.html`, `usine/comprendre/ia.py`, `conception/essai-exemples-a-l-aveugle.md` (nouveau) | 19 nov 2026 | 19 nov 2026 | décisions d'Arthur du 19 nov |
| Codex (OpenAI) | `dialogue/LISEZMOI.md`, `AGENTS.md`, `conception/LISEZMOI.md`, `USINE.md` §4 | 19 nov 2026 20 h 52 | 19 nov 2026 20 h 53 | les règles après la décision |
| Claude Code | `conception/contrat-noms-ecran.md` (version 2), `USINE.md` (l'étape 1, l'inconnue n° 1), `conception/essai-boite.md` (la note du §11) | 19 nov 2026 | 19 nov 2026 | la vérification du contrat ; la vérification de la boîte |
| Claude Code | `conception/contrat-noms-ecran.md` (version 3), `USINE.md` (le registre n° 63, la boîte, l'étape 2), `conception/essai-boite.md`, `conception/carte-de-l-usine.html`, `conception/LISEZMOI.md` et `dialogue/LISEZMOI.md` (la proportionnalité) | 19 nov 2026 | 19 nov 2026 | le contrat ; la boîte ; les règles |
| Claude Code | `conception/contrat-noms-ecran.md` (le morceau 12 précisé), `USINE.md` (le registre n° 63 reformulé) | 19 nov 2026 | 19 nov 2026 | le contrat |
| Claude Code | `conception/contrat-noms-ecran.md` (aligné : « transmis » ; exemple d'essai dédié ; union sportive adaptée) | 19 nov 2026 | 19 nov 2026 | le contrat |
