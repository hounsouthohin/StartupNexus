# Les exemples de l'usine

Des descriptions d'app qui servent de **preuves rejouables** : chacune se fabrique avec
`python -m usine fabriquer usine/exemples/<nom>.json`, et ses juges peuvent être re-prouvés par
sabotage (`usine/preuve_regles.mts`, `usine/preuve_ecrans.py`).

| Fichier | Origine | Ce qu'il prouve |
|---|---|---|
| `mediatheque.json` | écrite à la main (N1.0) | profil, catalogue public, collection avec circuit, lien vers une fiche |
| `types.json` | écrite à la main (N1.1) | les 11 types de champs, champs facultatifs, saisie à l'écran |
| `union-sportive.json` | **écrite par l'IA** (gpt-5.5, étude 05, version v2 des lecteurs) pour un vrai brief ; reprise par la répétition générale du 9 oct : un champ « nom » facultatif ajouté à chaque fiche (la v2 ne lisait pas les champs) et 3 exceptions retirées (états cités par leur libellé, défaut v2 corrigé depuis) | **registres** (7), circuits à 2 et 3 états, **suppression accordée**, un seul rôle connecté |

La médiathèque **écrite par l'IA du texte à l'app** (N1.1) n'est pas recopiée ici : elle se refait avec
`python -m usine comprendre … --nom mediatheque` (≈ 0,33 $).
