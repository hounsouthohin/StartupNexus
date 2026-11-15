# La montée de Next.js (16.4.0 → 16.4.6), et le contrôle des failles avant de fabriquer

> **Taille** : petit · **Statut** : fini (à clore par Arthur)
> **Dates** : écrit le 13 nov 2026 · validé par Arthur le 13 nov (« oui je donne mon accord ») · fini le 13 nov

## Avant : la conception

### 1. En bref
Depuis le 13 novembre, `next build` refuse de construire : la version de Next.js figée dans le squelette de l'usine
(16.4.0) a des failles connues. Toute fabrication s'arrête donc à l'étape 8 sur 10. On monte en 16.4.6, qui les corrige.
On corrige aussi la classe du problème : l'usine contrôlera elle-même les failles connues de ses dépendances avant de
fabriquer.

### 2. À quoi ça sert
Sans cela, l'usine ne fabrique plus rien. Et sans le contrôle, une faille dans une autre bibliothèque que Next (qui
n'a pas sa propre garde) passerait en silence dans chaque app.

### 3. Ce qui existe déjà
- `usine/modele-app/package.json` et `package-lock.json` : les versions figées du squelette, copiées dans chaque app.
- `usine/assembler.py`, étape 5 : `npm ci --prefer-offline --no-audit` installe depuis le fichier de verrouillage, en
  désactivant exprès l'audit.
- `npm audit` (l'outil établi de npm) le 13 nov :
  - **next 16.4.0** : 2 critiques (exécution de code à distance par l'optimisation d'images SVG, et par les fonctions
    `use cache`, que le squelette utilise) et 1 haute (déni de service par les Server Actions) ; corrigé en 16.4.6 ;
  - **zod 4.6.5** (utilisé par ZenStack à l'exécution) : 1 haute ; corrigé en 4.6.6 ;
  - **hono 4.13.13**, par ZenStack : moyennes ; corrigé en 4.13.16 ;
  - **deepmerge-ts**, par Prisma et l'outil de ZenStack : 1 haute, sans correctif (outil de développement, non exposé).

### 4. Comment on la construit
- **La montée** : `npm install next@16.4.6 --save-exact`, puis `npm audit fix` sans `--force`, qui corrige zod et hono
  sans changement majeur. On liste ensuite exactement les paquets dont la version a changé.
- **Le contrôle** : une fonction `auditer` dans l'assembleur, au début de l'étape 5. Elle lance
  `npm audit --package-lock-only --json` sur le fichier de verrouillage de l'app, sans rien installer.
  - Une faille **critique** arrête la fabrication, avec un message clair.
  - Une faille **haute** est inscrite dans le journal et dans le rapport de l'app, sans bloquer.
  - **Sans réseau**, l'audit est dit « non fait », visiblement, et la fabrication continue. Ce n'est jamais un
    « accepté » silencieux.
- **Alternatives écartées** :
  - rester en 16.4.0 en contournant la garde de Next : non, c'est une vraie faille ;
  - écrire une liste de versions interdites à la main : solution maison fragile ; `npm audit` lit le registre officiel
    des failles.

### 5. Les pièges et leurs parades
- **Un changement de comportement** dans une version corrective : les juges de trois apps le verraient (preuve ci-dessous).
- **Un audit sans réseau** qui laisserait passer : il est dit « non fait », jamais « accepté ».
- **Un audit qui change avec le temps**, quand une nouvelle faille est publiée : c'est voulu. L'usine s'arrêtera alors
  avec un message, comme `next build` l'a fait.
- **Modifier le squelette pendant une répétition** : aucune répétition n'est en cours.

### 6. Comment on prouve qu'elle marche (écrit avant le code)
- **Le contrôle** (`usine/preuve_audit.py`) :
  - **sabotage** : le fichier de verrouillage d'avant (commit `8d4e288e`, Next.js 16.4.0) doit être **refusé**, avec
    `next` parmi les paquets critiques ;
  - **témoin** : le squelette après la montée doit être **accepté** (0 critique) ;
  - **sans réseau** : registre injoignable, le résultat doit être « non fait ».
  - Lancée **avant** la montée, la preuve doit aussi refuser le squelette actuel : le contrôle voit le vrai problème.
- **La montée** :
  - médiathèque, app des types et union sportive fabriquées **au vert** (règles toutes conformes, écrans tous passés) ;
  - la preuve des écrans par sabotage : tous les sabotages attrapés, témoin vert ;
  - la preuve des règles par mutation : aucun survivant hors des familles connues (sans effet, ou relire / modifier ses
    fiches après perte du rôle).
- **Le critère d'arrêt** : un seul juge qui change d'avis, et je m'arrête pour comprendre, sans rien assouplir.

### 7. Le périmètre
- **Touché** : `usine/modele-app/package.json`, `package-lock.json` ; `usine/assembler.py` (la fonction `auditer` et son
  branchement) ; `usine/preuve_audit.py` (nouveau).
- **Pas touché** : traducteurs, juges, pièces d'écran, Description.
- **Taille max** : une demi-journée.
- **Risque** : faible.

### 8. Questions pour le relecteur
Aucune : petite pièce, validée par Arthur sans relecture extérieure.

## Relecture

Sans objet (petite pièce). Décision d'Arthur : go, le 13 nov.

## Après : le compte rendu

### 9. Ce qui a été fait
- `usine/modele-app/package.json` : `next` 16.4.0 → **16.4.6**, version exacte.
- `usine/modele-app/package-lock.json` : **13 paquets changés sur 311**, tous dans des versions correctives :
  - la famille Next (`next`, `@next/env`, et les 8 compilateurs `@next/swc-*`) : 16.4.0 → 16.4.6 ;
  - `zod` 4.6.5 → 4.6.7 ;
  - `hono` 4.13.13 → 4.13.18 ;
  - `@hono/node-server` 1.19.17 → 1.19.19.
- `usine/assembler.py` :
  - nouvelles fonctions `auditer` et `resume_audit` ;
  - l'étape 5 audite **avant** d'installer, s'arrête sur une faille critique, et écrit le bilan dans le journal et dans
    le rapport de l'app (`99-rapport.json`, clé `audit`) ;
  - `npm ci` garde `--no-audit` : l'audit est fait une seule fois, par notre fonction.
- `usine/preuve_audit.py` (nouveau) : la preuve du contrôle.

### 10. Les écarts avec la conception
- `npm audit fix` a pris **zod 4.6.7** (au lieu de 4.6.6) et **hono 4.13.18** (au lieu de 4.13.16) : ce sont les dernières
  versions correctives permises. Aucun autre écart.
- Il reste 5 failles connues, **aucune critique** :
  - 4 hautes, toutes dues à `deepmerge-ts` (épuisement de la pile sur des objets récursifs), par les outils en ligne
    de commande de Prisma et de ZenStack : aucun correctif n'existe ; ce sont des outils de fabrication, absents de l'app
    qui tourne ;
  - 1 moyenne : `@hono/node-server`, par l'outil de ZenStack ; le correctif demande une version majeure que ZenStack
    n'accepte pas encore.
  Elles sont écrites dans le rapport de chaque app, et on les revoit à la prochaine version de ZenStack.

### 11. Les résultats des preuves (contre les seuils écrits d'avance)

| Preuve | Seuil | Résultat |
|---|---|---|
| Contrôle des failles, **avant** la montée | le sabotage et le squelette d'alors refusés ; sans réseau = « non fait » | ✔ sabotage refusé (`next`) ; squelette 16.4.0 refusé ; sans réseau : « non fait » |
| Contrôle des failles, **après** la montée | 3 cas sur 3 | ✔ **3/3** (sabotage refusé, témoin accepté avec 0 critique, sans réseau « non fait ») |
| Médiathèque | au vert | ✔ règles **120/120** ; écrans **11 passés, 1 sauté** (voir plus bas) |
| App des types | au vert | ✔ règles **267/267** ; écrans **17 passés** |
| Union sportive | au vert | ✔ règles **212/212** ; écrans **28 passés** |
| Preuve des écrans par sabotage (médiathèque) | tous attrapés, témoin vert | ✔ **8/8** attrapés ; le témoin passe |
| Preuve des règles par mutation (médiathèque) | aucun survivant hors des familles connues | ✔ 57 mutants : 35 tués, 22 survivants, tous classés (ci-dessous) |

- **Le test d'écran sauté** : « création : ouvrage ». Sa raison est écrite dans le juge : aucun rôle connecté ne crée
  d'ouvrage dans cet exemple, car le catalogue vient des données de départ. Ce saut vient de l'exemple, pas de la
  montée de version.
- **Les 22 survivants de la preuve des règles**, tous dans les familles connues :
  - **16 sans effet** :
    - 6 règles de lecture ou d'interdiction redondantes sur les ouvrages, que tout le monde lit et que personne ne
      modifie ni ne supprime ;
    - 1 interdiction de suppression sur l'adhérent, que personne ne peut supprimer ;
    - 1 condition « l'ouvrage est visible », toujours vraie ;
    - 5 règles **masquées** l'une par l'autre (« seul le bibliothécaire modifie » contre les règles d'étape) ;
    - 3 sur l'interdiction de re-désigner un ouvrage invisible, qui ne peut pas arriver puisque tout ouvrage est
      visible ;
  - **6 de la famille « perte du rôle »** : 4 pour relire ses propres fiches (toléré) et 2 pour **modifier son profil**
    après avoir perdu son rôle (critique, réservé au futur juge par modèle, étape 3).
  - Bilan : **35 erreurs attrapées sur 41 qui ont un effet (85 %)**. C'est exactement le chiffre relevé pour la
    médiathèque en octobre (testeur v1.2 : 35/41). Le juge des règles se comporte comme avant.
- **Observation** : la preuve des écrans a duré **69 minutes** (une construction complète de l'app par sabotage). Ce
  n'est pas un défaut de 0b, mais c'est un budget de temps à surveiller à l'étape 3.

Pour rejouer :
- `python -m usine.preuve_audit`
- `python -m usine fabriquer usine/exemples/<mediatheque|types|union-sportive>.json --essai`
- `python -m usine.preuve_ecrans runs/<n°>`
- `npx tsx <dépôt>/usine/preuve_regles.mts`, depuis le dossier `app/` d'une fabrication

### 12. Ce qu'Arthur peut voir lui-même
- `python -m usine.preuve_audit` : trois lignes cochées, dont celle où l'ancien squelette est refusé à cause de `next`.
- `python -m usine demarrer runs/20261113-155723-mediatheque`, puis ouvrir l'adresse affichée. La médiathèque tourne
  sur Next.js 16.4.6 : connecte-toi comme adhérent, demande un emprunt ; comme bibliothécaire, accepte-le. La première
  fois, les dépendances se réinstallent (vérifié le 13 nov : l'app répond en 25 s, réinstallation comprise).

### 13. Ce qui reste
- Registre n° 60 inscrit (`USINE.md` §7). Inconnue n° 10 fermée : Next.js 16.4.6 marche avec ZenStack 3.9.7.
- `deepmerge-ts` et `@hono/node-server` : à revoir à la prochaine version de ZenStack.
- Le contrôle demande le réseau. Dans la future boîte (étape 1.1), il se fera **à la construction de l'image figée**,
  pas dans la boîte.
