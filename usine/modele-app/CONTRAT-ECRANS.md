# Le contrat des noms à l'écran — la notice de l'artisan

> Pour qui écrit des écrans dans cette app (l'artisan, dans `sur-mesure/`). Le dossier complet, avec ses raisons et ses
> preuves : `conception/contrat-noms-ecran.md` du dépôt de l'usine.

**Pourquoi.** Un juge indépendant joue l'app comme une personne : il se connecte, ouvre le menu, clique sur des boutons
**par leur nom**. Il tire ces noms de la description validée par le client, jamais de ton code. Si ton écran affiche un
autre nom, ou cache un état, le juge conclut « introuvable » ou « non jugé ». Ton travail n'est pas coché.

**Où sont les noms.** Dans `lib/notice.ts` et `lib/droits.ts`, produits par l'usine depuis la description. **Lis-les là,
ne les écris jamais en dur**, ne les reformule pas.

## Les onze règles

1. **Connexion d'essai** : chaque bouton de connexion simulée contient l'identifiant de la personne, en mot entier
   (`personne 1 · adherent_1`). Le visiteur : `visiteur (non connecté)`. Ne touche pas à l'accueil.
2. **Menu** : dans `<nav>`, un lien par fiche, au nom de la liste (`titre` de la notice, « Emprunts »).
3. **Repère de page** : un seul `<h1>` visible. Une liste : son nom (« Emprunts »). Une fiche : sa sorte, puis son titre
   (« Emprunt : Germinal ») ; utilise `titreDe(fiche, ligne)` de `components/vues.tsx`.
4. **Bouton de création** : exactement `creation.libelle` de la notice.
5. **Boutons d'étape et création en un clic** : exactement `etat.boutons[<état d'arrivée>]` et `actionsLigne[].libelle`.
6. **Le titre d'une fiche** : dans une liste, c'est le **premier morceau** de la ligne, et c'est **le lien qui ouvre
   cette fiche-là** (`/f/<Fiche>/<id>`), au texte exactement égal au titre. Il n'est pas promis unique.
7. **Libellé des états** : celui de `etat.libelles`, et rien d'autre.
8. **Champs** : une `<label for>` reliée au champ par son `id`, au texte exactement égal au libellé ; des identifiants
   uniques même si plusieurs formulaires sont ouverts (`useId`) ; « (facultatif) » et les aides passent par
   `aria-describedby`. Les listes de choix aussi.
9. **Un nom, une action** : dans une même ligne, ou une même page pour les actions de page, deux éléments ne portent
   jamais le même nom. N'appelle pas tes boutons « Créer », « Modifier », « Supprimer » ou « Enregistrer » pour une autre
   action que celle de l'app.
10. **Pas de règle cachée** : n'ajoute aucune règle que la description ne contient pas (un filtre, un refus, un champ
    obligatoire). Si tu en vois une qui manque, **signale-la** ; ne l'invente pas.
11. **L'état de chaque zone de données** (une liste, une fiche, une liste de choix) : elle porte `data-zone`,
    `data-fiche`, `data-etat` = `chargement`, `pret` ou `erreur`, et `aria-busy="true"` pendant le chargement. **Une
    erreur s'affiche comme une erreur, jamais comme une liste vide.** Utilise la pièce `Zone` de `components/pieces.tsx`,
    avec `etatZone(requête)` : elle fait tout cela.

## Deux conventions pour tous les noms

- **Le nom lu par la machine est le texte affiché.** Un `aria-label` ne dit jamais autre chose que ce que voit la
  personne. Le mieux : pas d'`aria-label` du tout sur un bouton qui a déjà son texte.
- **La forme exacte** : comparée à la lettre, majuscules comprises. Seule permise : la majuscule initiale d'un nom affiché
  seul (le menu, le titre d'une page).

## Ce qu'il faut savoir en plus

- **Next.js garde la page quittée cachée dans la page** (`display: none`). Ne compte jamais sur un élément caché : le juge
  ne regarde que ce qui est visible.
- **Le serveur refuse un texte obligatoire vide ou fait d'espaces.** Ton formulaire doit afficher ce refus comme un
  refus (le message du serveur), jamais comme un succès.
- **Les confirmations** sont des boutons sur place (« Confirmer la suppression »), pas des fenêtres du navigateur
  (`window.confirm`).
- **Les données** : seulement par le client de la personne connectée (`useClientQueries` de ZenStack, comme dans
  `components/pieces.tsx`), jamais par un accès direct à la base. Les droits sont dans le cœur ; tu ne les écris pas, tu
  ne les contournes pas.
