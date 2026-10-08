# Étude 03 — Essai 2 : la traduction matrice → règles tient-elle sur les cas durs ?

*7 octobre 2026. Suite de l'étude 02. Projet jetable : `poc/regles/` (l'usine n'a pas été touchée,
sauf 2 nouvelles matrices ajoutées au banc de la phase 3).*

## 1. La question

La médiathèque (étude 02) était simple. Avant de construire un traducteur automatique
« matrice → règles », il fallait savoir si la traduction reste **mécanique** sur les cas que la
médiathèque n'avait pas — ou si un cas est impossible.

## 2. Ce qui a été fait

5 entrées : 3 matrices de notre banc et **2 vrais briefs** (Codeur.com) dont j'ai d'abord écrit la
matrice à la main.

| Entrée | Cas testé | Vérifications | Résultat |
|---|---|---|---|
| notes de frais | plusieurs acteurs dans un circuit ; modifier seulement en brouillon | 90 | **90/90** |
| garage | le patron crée POUR le client ; profil d'un acteur invité | 90 | **90/90** |
| atelier partagé | fiches enfants ; catalogue géré ; catalogue privé vu au travers d'un public | 113 | **113/113** |
| agence de réservations (**vrai brief**) | 3 rôles ; suppression ; « pour son compte » ; admin qui gère tout | 108 | **108/108** |
| SAV dépannage (**vrai brief**) | enfants sur 3 niveaux, avec circuits d'états ; tables de choix ; lien facultatif | 78 | **78/78** |
| **Total** | | **479** | **479/479** |

Les vérifications ne sont **pas écrites à la main** : un testeur générique (`poc/regles/run.ts`) lit
la matrice attendue et essaie chaque case, rôle par rôle (voir, voir par identifiant forcé, créer,
créer au nom d'un autre, créer dans un état avancé, modifier dans chaque état, changer le
propriétaire, chaque flèche possible du circuit, supprimer). C'est le premier morceau des « tests
par rôle générés » du niveau 1. Un refus causé par une erreur technique n'est jamais compté comme
un refus réussi : ce garde-fou a démasqué 52 faux succès au premier passage.

## 3. Réponse : oui, la traduction est mécanique

Aucun cas impossible. **11 patrons** de traduction couvrent les 5 cas :

| # | Dans la matrice | Règle ZenStack |
|---|---|---|
| 1 | qui est connecté | `type Auth { id, role } @@auth` (fourni par Clerk) |
| 2 | profil | `userId @unique @default(auth().id)` ; créer / voir / modifier le sien ; `userId` immuable |
| 3 | catalogue (public ou non), géré par X | lire : `true` (public) ou **la liste des rôles déclarés** ; créer / modifier : rôles gestionnaires. ⚠️ Corrigé par l'étude 04 : `auth() != null` (« tout connecté ») laissait lire un inconnu qui se crée un compte |
| 4 | collection, propriétaire P | `ownerId @default(auth().id)` ; voir les siens ou tout selon la case ; propriétaire immuable |
| 5 | saisie pour autrui | créer réservé au rôle qui saisit ; le propriétaire ne fait que voir |
| 6 | circuit d'états | état initial obligatoire à la création ; **une règle par flèche** (`before().status == a && status == b`), les autres champs inchangés |
| 7 | modifier seulement dans certains états | une règle « état inchangé » par état autorisé |
| 8 | enfant | voir : `check(parent)` (+ connecté si l'enfant n'est pas public) ; gérer : `check(parent, 'update')` — marche sur 3 niveaux |
| 9 | voir au travers de V | `relation?[true]` + la condition de lecture de V pour cet acteur |
| 10 | supprimer (exception citée) | `@@allow('delete', …)` ; sinon rien = refusé |
| 11 | table de choix | un **modèle de données** (pas une liste figée dans le code) |

## 4. Ce que l'essai a trouvé

**Deux règles de sécurité absentes de la matrice, à ajouter systématiquement au traducteur :**

1. **Clôture à la création** — ZenStack ne vérifie pas qu'on a le droit de *voir* la fiche qu'on
   pointe. Traduite littéralement, la matrice laissait un prestataire créer une réservation sur le
   client d'un autre prestataire, en donnant son identifiant. Correction mécanique :
   `check(client, 'read')` pour chaque fiche pointée.
2. **Cohérence des propriétaires** — le patron pouvait créer la réparation du client A sur le
   véhicule du client B (le client B aurait vu une réparation qui n'est pas la sienne). Correction
   mécanique : si deux fiches liées appartiennent au même rôle, ce doit être la même personne
   (`vehicle.ownerId == ownerId`).

**Un bug de ZenStack 3.9.7** : comparer un champ d'état à sa valeur d'avant
(`status == before().status`) provoque une erreur SQL. Contournement mécanique : nommer l'état
(patron 7). À signaler à ZenStack ; illustre le risque « dépendance » (§4.9 d'USINE.md).

**Des trous dans le vocabulaire de la matrice (phase 3)**, alors que les règles, elles, savent faire :

| Trou | Où | Conséquence aujourd'hui |
|---|---|---|
| un enfant ne peut pas avoir de circuit d'états | SAV (interventions, actions) | le calculateur refuse ; contourné en « collection », 4 écarts |
| pas de fiche « partagée par toute l'équipe » | SAV | une collection donne « les siens » ; faux dès 2 comptes |
| pas de préréglage « administrateur qui gère tout » | agence | 6 exceptions pour une seule phrase du brief |
| un seul rôle propriétaire par fiche | agence (« pour son compte ») | le gestionnaire qui réserve pour lui n'est pas exprimable |

L'agence a demandé **13 exceptions** (moyenne du banc : 0,8). Les vrais briefs à plusieurs rôles
mettent nos préréglages à l'épreuve : les 4 trous ci-dessus sont la liste de travail.

**Une question pour le miroir, confirmée en vrai** : le gestionnaire crée des réservations mais ne
voit pas les fiches clients (sauf celles déjà réservées). Le calculateur l'avait signalé ; l'essai
le confirme. C'est au client de trancher.

## 5. Limites de l'essai (honnêtement)

- **C'est moi qui ai appliqué les patrons, à la main.** L'essai prouve que la traduction *peut* être
  mécanique ; seul le traducteur automatique (niveau 1) le prouvera vraiment.
- Les adaptateurs de test (`case.ts`, 30 à 50 lignes par cas : données de départ, données
  valides) sont écrits à la main ; dans l'usine, ils se déduiraient de la notice.
- Pas testé : « ses prestataires » (périmètre par relation, D2 — a priori une règle de plus sur un
  second champ, mais non vérifié) ; les écritures imbriquées (créer une réservation ET son client
  en une fois) ; la lecture des champs un par un ; les fiches liées à plusieurs (ajout / retrait).
- Le testeur vise une fiche par vérification, pas toutes.
- Prisma refuse, à juste titre, qu'une IA remette une base à zéro : chaque version de schéma a eu
  sa base neuve. Pour les apps livrées, **l'évolution de la base d'un client** sera un vrai sujet.

## 6. Ce que ça change pour la suite

- Le **traducteur matrice → règles** du niveau 1 est faisable : 11 patrons + 2 règles systématiques
  (clôture, cohérence).
- Le **vocabulaire de la matrice** doit s'étendre de 4 notions avant le niveau 1 (enfant à circuit,
  fiche d'équipe, administrateur global, plusieurs rôles créateurs), à vérifier sur le banc.
- Le **testeur générique** est réutilisable tel quel : c'est la base des tests par rôle livrés avec
  chaque app.

## Concepts utilisés

- **Délégation (`check`)** : une règle qui dit « fais comme pour le parent ». *Pourquoi* : un enfant
  hérite des droits de son parent sans recopier ses règles — si le parent change, l'enfant suit.
- **Clôture** : on ne peut choisir que ce qu'on a le droit de voir. *Pourquoi* : sinon, en devinant
  un identifiant, on rattache sa fiche à celle d'un autre (variante de l'IDOR vue en étude 02).
- **Contrainte de cohérence** : deux informations liées doivent concorder (la réparation et le
  véhicule ont le même propriétaire). *Pourquoi* : une règle d'accès juste sur des données
  incohérentes fuit quand même.
- **Test dérivé** : un test produit à partir d'une description (ici la matrice) au lieu d'être écrit
  à la main. *Pourquoi* : chaque nouvelle app reçoit ses tests sans effort, et ils disent
  exactement ce que le client a validé.

## Rejouer

```
docker start temporal-postgresql
cd poc/regles
.\prepare.ps1 <cas>          # notes-frais, garage-atlas, atelier-partage, agence-reservations, sav-depannage
npx tsx run.ts <cas>
```
Bases créées : `poc_regles_<cas>_<empreinte>` (une par version de schéma, toutes jetables).
