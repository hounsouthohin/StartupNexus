# Réponse finale des relectures — contrat d'accessibilité (A) et essai du juge d'écrans (B)

> 16 nov 2026 · Synthèse de deux relectures : Claude en ligne, et une seconde IA d'un autre fournisseur.
> La seconde IA a d'abord relu sans les dossiers, puis a refait sa relecture avec les dossiers complets.
> Ce texte est la décision consolidée ; les deux relectures complètes sont archivées à part.

## 1. Ce qui est décidé

| Décision | Position des deux relecteurs |
| --- | --- |
| Le contrat d'accessibilité passe en priorité | **Oui**, unanime. C'était l'issue écrite d'avance dans le dossier B |
| Le dossier A peut être développé, après les corrections du §2 | **Oui**, unanime |
| L'inspecteur sans IA reste l'approche du juge d'écrans | **Oui**, unanime |
| L'architecture de l'usine change | **Non** |
| L'essai B prouve que le juge d'écrans est qualifié | **Non**, unanime. Il prouve une faisabilité, pas une admission |
| On perfectionne l'inspecteur jetable avant de faire le contrat | **Non** : on corrige le compte rendu, on ne reconstruit pas l'essai |

**Verdicts retenus :**
- **Dossier A : OK avec corrections.**
- **Dossier B : à corriger avant clôture.** La seconde IA écrit « À revoir », Claude « OK avec corrections ». La
  différence porte sur la formulation, pas sur le fond : les deux demandent le même travail (§3). L'essai n'est clos que
  quand ce travail est fait.

## 2. Dossier A — les corrections à intégrer avant de coder

1. **Trois règles de plus**, présentées comme des **conventions du squelette** (pas comme des exigences du W3C) :
   - **le repère de page** : chaque page de liste porte un titre principal égal au nom pluriel de la fiche ; chaque page
     de fiche porte le titre de la fiche. L'inspecteur attend ce repère avant de compter les éléments ;
   - **le libellé des états** : un état s'affiche avec le libellé de la description, rien d'autre ;
   - **le lien de titre** : son nom est exactement le titre, sans préfixe ni suffixe (le cas « Vidéo test : … »).
2. **L'unicité des noms se vérifie dans le contexte d'une action**, pour un rôle et un état donnés : la ligne, la fenêtre
   de dialogue, ou la page pour les actions de page (création, étapes, créations en un clic). Deux boutons « Modifier »
   dans deux lignes différentes sont permis. Le contrôle par fiche seul ne suffit pas : une page de fiche peut réunir
   des boutons de plusieurs fiches.
3. **Le titre n'est pas promis unique**, et le modèle de données n'est jamais restreint pour faciliter un test.
   - L'inspecteur trouve d'abord **exactement une** ligne (il le vérifie : sinon « ambigu »), puis le lien du titre
     dans cette ligne.
   - La ligne se reconnaît par l'étiquette unique des données d'essai. Quand le titre vient d'une fiche désignée (un
     emprunt et son livre), et qu'un parcours a besoin de deux fiches au même titre, la ligne se reconnaît par une
     seconde valeur visible et distincte (la personne, la date).
   - « Le premier champ texte » exclut le **texte long**.
4. **Le champ « Libellé » ajouté en dernier recours** change le modèle de données et les formulaires. Il n'est permis
   que s'il est visible et validé au miroir **avant** la fabrication, jamais ajouté au moment de traduire. (Le dossier
   le prévoit déjà ; l'écrire comme une règle.)
5. **Les champs** : étiquette reliée par `for` et `id`. « (facultatif) » et les aides vont dans la description
   accessible (`aria-describedby`), pas dans le nom. C'est une convention de l'usine, justifiée par ce que l'essai a
   observé sur notre squelette ; l'enveloppement reste valide en HTML.
6. **Le nom accessible et le texte visible** : une fois un élément trouvé par son nom accessible, l'inspecteur vérifie
   aussi que son texte visible correspond. Sinon, un `aria-label` pourrait montrer au client autre chose que ce qu'il a
   validé (règle W3C « Label in Name »).
7. **La couverture du miroir est prouvée par sabotage** : on retire un nom du bloc « À l'écran » d'un exemple, et le
   contrôle doit échouer en nommant ce nom. Le contrôle compare les noms **que l'inspecteur cherchera** (tirés des
   parcours) au **texte rendu** du miroir, pas la description à elle-même.
8. **L'empreinte de la description**, calculée sur une forme canonique du JSON, est comparée à la **référence
   enregistrée par la porte** lors de la validation au miroir. Ni l'app ni le juge ne fournissent cette référence. Le
   juge refuse de juger si elle ne concorde pas.
9. **Les sabotages manquants** : un lien du menu renommé, un bouton d'étape renommé, un repère de page renommé (chacun →
   « introuvable »), et un filtre caché ajouté à une liste (→ « comportement faux »). Pour le filtre, les données de
   départ doivent contenir une fiche que le filtre exclut à tort, sinon le sabotage ne prouve rien.
10. **La règle 7 (pas de règle cachée)** est une obligation du constructeur. Les parcours vérifient certaines de ses
    manifestations ; ils ne prouvent pas l'absence de toute règle cachée. Le dossier doit le dire ainsi.
11. **Un numéro de format** dans la description : le refus d'une ancienne description dit « format 1, attendu 2 ».
12. **La normalisation des noms** : espaces et casse sont normalisés dans la description, selon la façon dont
    Playwright compare réellement (correspondance exacte sensible à la casse ; espaces normalisés).
13. **Les fenêtres de confirmation** : si une étape ouvre une fenêtre « Confirmer ? », l'inspecteur cherche d'abord dans
    la fenêtre ouverte, et vérifie qu'elle correspond à l'action attendue.

**Criticité** : élevée (l'entrée de toute la chaîne et le contrat d'un juge). Le compte rendu de A passera en relecture
extérieure.

## 3. Dossier B — ce qu'il faut corriger avant de clore

**Une seule action technique :**

1. **Rattacher les résultats à une version unique.** Si toutes les passes finales, les témoins du rejeu et les
   sabotages n'ont pas été rejoués après la dernière des trois corrections, **les rejouer** (`python juge.py … --passes 3`
   et `python saboter.py`). Inscrire dans chaque fichier de résultats les empreintes de l'inspecteur, de l'app, de la
   description et des données de départ, ainsi que la version de Chromium.

**Le reste est la réécriture honnête du compte rendu :**

2. **Trois résultats séparés pour l'app mixte** : sans repli, avec replis, et le nombre de parcours qui dépendent de
   chacun des **trois** replis (connexion, bouton de création, et reconnaissance d'un champ par le début de son
   libellé). Les replis se chevauchent : donner les nombres de parcours, pas une somme. Le tableau ne met pas ✔ là où
   le seuil écrit n'est atteint qu'avec des replis.
3. **Les sabotages** : « cinq sabotages initiaux attrapés, et un scénario de remplacement attrapé ». La classe
   « présent mais inutilisable » (bouton désactivé ou recouvert) **n'est pas prouvée**.
4. **La durée** : 150 s sur l'app mixte, au-delà du seuil de 120 s. Écrire ✗.
5. **Les échecs de l'app de l'agent, en catégories séparées** : 2 « introuvable » (noms absents de la description), le
   filtre des devis (règle non validée), les vidéos (titre non défini par le contrat), et 7 « non jugé ». Les « non
   jugé » ne comptent ni comme échecs ni comme réussites.
6. **Les vidéos** sont reclassées « affichage non conforme au contrat » — dans cet essai, un trou du contrat — **à
   condition** de vérifier dans les résultats que la base contenait bien les bonnes fiches. Sinon, garder
   « comportement faux ».
7. **Le filtre des devis** : confirmer que les données de départ contenaient au moins un devis non confirmé, visible
   par ce rôle, que l'écran aurait dû proposer. Sans ça, le parcours ne prouve pas le filtre ; seul le code le montre.
8. **La conclusion**, réécrite ainsi :
   > L'essai montre qu'un inspecteur sans IA peut jouer ces parcours, et certaines interdictions, sur des apps
   > construites différemment, à condition que les noms d'interface soient définis d'avance. Les adaptations
   > nécessaires confirment la priorité du contrat d'accessibilité. L'inspecteur n'est pas encore admis : il le sera
   > dans le vrai juge, avec ses propres preuves.

## 4. À inscrire pour le vrai juge (plus tard, pas maintenant)

- un témoin de rejeu pour une **modification** (PUT, PATCH), pas seulement des créations et une confirmation ;
- **la preuve que la session interdite est bien reconnue** par le serveur avant le rejeu (par exemple, une page qui
  affiche l'identifiant de la personne connectée) ;
- la preuve de la classe « présent mais inutilisable », avec un **témoin proche** : un bouton désactivé légitimement
  (tant qu'un champ obligatoire est vide) ne doit pas être signalé ;
- des **données de départ qui respectent les règles de l'app** : préparées par la couche de données de l'app plutôt
  que par du SQL brut, ou vérifiées contre ses invariants ;
- l'**isolement des données** si les parcours tournent en parallèle (une base par fil, ou rester séquentiel) ;
- **aucune donnée réelle dans les traces** : la visionneuse les lit localement, mais les traces contiennent la page,
  les requêtes et leurs contenus ;
- des parcours propres, avec leur oracle, pour les **écrans riches** (recette des capacités).

## 5. Les désaccords entre relecteurs, et comment ils sont tranchés

| Sujet | Claude | Seconde IA | Retenu |
| --- | --- | --- | --- |
| Unicité des noms | par écran | dans le contexte d'une action | **le contexte d'une action** (§2, point 2) |
| Données d'essai pour les titres répétés | une fiche désignante par fiche désignée | ne pas restreindre ; identifier la ligne autrement | **identifier la ligne par une seconde valeur visible** (§2, point 3) |
| Les vidéos | trou du contrat | défaut d'affichage, à ne pas minimiser | **trou du contrat dans cet essai ; défaut réel une fois le contrat écrit** (§3, point 6) |
| Verdict de B | OK avec corrections | À revoir | **à corriger avant clôture**, même travail dans les deux cas |
| Rejeu « critique » (1re lecture de la seconde IA) | déjà traité | retiré après lecture des dossiers | **clos** : le témoin du rejeu existait (9/9, 6/6, sabotage n° 6) |

**Décision d'Arthur** : …
