# Étude 06 — E6 : la plomberie des écrans, Refine ou nos propres pièces ?

*7 octobre 2026. Projet jetable : `poc/ecrans/`. L'usine n'a pas été touchée. Coût d'IA : 0 $.*

## 1. La question

Toutes les pièces d'écran de l'usine (liste de fiches, fiche détail + bloc de décision, mon profil…)
reposeront sur une « plomberie » : aller chercher les données, écrire, cacher ce qui est interdit.
Deux candidats : **A — Refine** (cadre « sans habillage », retenu à titre provisoire en étude 01)
ou **B — nos propres pièces** sur les fonctions que **ZenStack génère depuis le schéma**
(`@zenstackhq/tanstack-query`). Ce choix engage toutes les pièces : il valait un essai.

## 2. Le dispositif (comparaison à armes égales)

La médiathèque (matrice de référence), **mêmes écrans deux fois**, dans la même app :
- **partagé** : le schéma et ses règles (patrons des études 03-04), l'API ZenStack, la **notice**
  (fiches, champs, libellés — typée avec les types générés par ZenStack), la matrice des droits
  côté écran, et tout l'**affichage** (tableau, fiche, boutons, formulaire) ;
- **différent** : seulement la plomberie — `components/a/pieces.tsx` (Refine) et
  `components/b/pieces.tsx` (nos pièces).

Les pièces sont **génériques** : `ListeDeFiches`, `FicheDetail` (avec bloc de décision) et
`MonProfil` reçoivent un nom de fiche et lisent la notice. Connexion simulée par un cookie (Clerk,
déjà validé par la PoC, n'est pas ce qu'on compare).

## 3. Résultats

| Critère | A — Refine | B — nos pièces sur ZenStack |
|---|---|---|
| Tests par rôle Playwright (visiteur, adhérent, bibliothécaire) | **3/3** | **3/3** |
| Lignes de plomberie | 123 | **90** (−27 %) |
| Adaptateur à écrire et maintenir | oui (Refine → API ZenStack : il n'en existe pas d'officiel) | **non** (mêmes auteurs que l'API) |
| Dépendances ajoutées (en plus de TanStack Query, commun aux deux) | Refine : 3,9 Mo | ZenStack : **0,2 Mo** |
| Un champ **renommé** dans le schéma est signalé à la compilation | oui *si* le type a été déclaré à la main | **oui**, automatiquement |
| Un **oubli dans la requête** (lien non demandé, puis affiché) est signalé | **non** — l'app plante à l'exécution | **oui** — erreur de compilation |
| Activité du projet | aucune version depuis avril 2026 | publie chaque semaine |
| Failles connues (dépendances de l'app) | 0 | 0 |

**Le typage, en clair** : avec Refine, on *déclare* le type de ce qu'on reçoit — le compilateur
croit sur parole. Avec ZenStack, le type est *déduit de la requête* : si on ne demande pas l'ouvrage
lié, le compilateur sait qu'il n'est pas là. Un renommage de champ, lui, est attrapé dans les deux
cas, grâce à la **notice typée** (qui porte presque tous les noms de champs des pièces génériques).

## 4. Décision

**On garde B : nos propres pièces, sur les fonctions générées par ZenStack. Refine est écarté.**
Même comportement, moins de code, pas d'adaptateur, une dépendance de moins (et en perte de vitesse),
un typage plus sûr sur le code spécifique.

## 5. Ce que la décision coûte (honnêtement)

- **Ce que Refine faisait et qu'il faudra écrire** : la gestion de la pagination, des filtres et du
  tri dans les listes (Refine fournit ces « états de tableau »), les notifications, la synchronisation
  avec l'adresse de la page. Quelques dizaines de lignes chacun, sur TanStack Query — à prévoir dans
  le catalogue de pièces du niveau 1.
- **Concentration** : données, règles ET plomberie viennent de ZenStack. Porte de sortie : les
  fonctions générées sont une fine couche sur TanStack Query et sur l'API RPC (`/api/model/...`) ;
  on peut les remplacer par des appels directs sans toucher aux pièces.
- **Les pièces génériques ne sont pas typées à l'intérieur** (le nom du modèle vient de la notice) :
  la sécurité de type vient de la notice typée. Dans l'usine, la notice sera produite par programme
  depuis la matrice, avec ce même typage.

## 6. Découvertes en route

- **Next.js 16.4 active par défaut le « cache des composants »** : tout ce qui lit la session doit
  être derrière un `<Suspense>` (patron officiel appliqué). Les pièces de l'usine devront le
  respecter — encore un changement de version qui casse (étude 02).
- La séparation **notice / affichage / plomberie** s'est révélée naturelle : c'est probablement la
  bonne architecture des pièces du niveau 1 (l'affichage partagé n'a pas bougé entre A et B).

## Concepts

- **Plomberie** : le code qui relie l'écran aux données (lire, écrire, rafraîchir, cacher).
  *Pourquoi* : c'est elle que toutes les pièces partagent ; la choisir mal coûte partout.
- **Type déclaré vs type déduit** : déclaré = on affirme ce qu'on reçoit ; déduit = le compilateur
  le calcule depuis la requête. *Pourquoi* : seul le second attrape les oublis.
- **Notice typée** : la description des fiches dont chaque nom de champ est vérifié contre le schéma.

## Rejouer

```
docker start temporal-postgresql
cd poc/ecrans
.\prepare.ps1 ; npx tsx --env-file=.env.local scripts/seed.ts
npx next build ; npx next start -p 3200      # http://localhost:3200 — variantes /a et /b
npx playwright test                          # les 6 tests par rôle
npx tsc -p tsconfig.typage.json --noEmit     # l'expérience de typage (erreur attendue dans b-oubli)
```
