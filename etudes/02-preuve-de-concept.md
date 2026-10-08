# Étude 02 — Preuve de concept : la médiathèque assemblée à la main

*5 octobre 2026. Suite de l'étude 01. Projet jetable : `poc/mediatheque/` (l'usine n'a pas été touchée).*

## 1. Ce qui a été fait

L'app de la médiathèque, montée à la main avec **ZenStack v3** (données et droits), **Refine v5**
(écrans) et **Clerk v7** (comptes), sur Next.js 16. Les droits viennent de la matrice de
référence (`harness/matrices/mediatheque.expected.yaml`), recopiée deux fois à la main : en règles
ZenStack (`zenstack/schema.zmodel`) et en tableau lu par l'écran (`lib/matrix.ts`).

| Vérification | Comment | Résultat |
|---|---|---|
| Règles côté serveur, rôle par rôle | script contre la base (`scripts/test-policies.ts`) | **35 / 35** |
| Bout en bout par HTTP, vraies sessions Clerk | `scripts/test-http.ts` | **11 / 11** |
| Écrans par rôle (menus, boutons) | tests navigateur Playwright + captures (`e2e/`) | **3 / 3** |
| Audit de sécurité des paquets de l'app | `npm audit --omit=dev` | **0 faille** |

Les 5 points de la fiche : (1) l'accès forcé est refusé par le serveur — page `/essais` : accepter
soi-même, créer un emprunt déjà accepté, ajouter un ouvrage, supprimer → tous refusés ; (2) menus et
boutons différents par rôle ; (3) circuit d'états respecté ; (4) « mon profil » créé
automatiquement ; (5) catalogue public sans compte. **Tous vérifiés.**

## 2. Les 5 inconnues de l'étude 01 — réponses

**1. ZenStack v2 ou v3 → v3** (3.9.7). Ce qui marche : l'utilisateur vient de Clerk sans table
« utilisateurs » (`type Auth @@auth`) ; le lien automatique vers le profil s'écrit
`@default(auth().id)`, sans code ; tout est refusé tant qu'une règle ne l'autorise pas.
Deux réserves :
- la v3 **n'a plus l'API « puis-je ? »** de la v2 (celle qu'utilisait l'article de 2024). L'écran ne
  peut donc pas demander à ZenStack s'il doit montrer un bouton : il lit la matrice. C'est acceptable
  **à condition que l'usine produise les deux traductions depuis la même matrice** — à la main,
  elles divergeraient vite ;
- les migrations (`zen db push`) passent encore par le moteur de Prisma (un `~schema.prisma` est
  généré). Prisma reste donc un outil de l'atelier, mais n'est plus utilisé quand l'app tourne.

**2. Les circuits d'états → oui, proprement.** Une règle par flèche du circuit :
```
@@allow('update', auth().role == 'bibliothecaire')            // qui peut toucher
@@allow('post-update', before().status == requested && (status == accepted || status == refused))
@@allow('post-update', before().status == accepted && status == returned)
@@deny('post-update', bookId != before().bookId || ownerId != before().ownerId)  // rien d'autre ne bouge
```
Essayés et refusés : sauter une étape, revenir en arrière, rouvrir un emprunt rendu, changer
l'ouvrage en acceptant. **Une tentative refusée n'écrit rien** (vérifié en relisant la base).
La traduction matrice → règles est mécanique : c'est exactement ce qu'un programme sait faire.

**3. Refine dans Next.js → ça marche, mais il apporte peu ici.** Build de production et tests
navigateur OK avec Next 16 et React 19. Mais, critique honnête :
- ce qu'il a fourni : des fonctions d'accès aux données avec cache, la liste des ressources pour le
  menu, la mécanique « masquer si interdit ». L'adaptateur vers ZenStack (72 lignes) et la logique
  des droits, c'est moi qui les ai écrits ;
- **les types ne sont pas reliés au schéma** : on écrit `useList<Book>` à la main ; si le schéma
  change, rien ne prévient. Cela contredit notre exigence de pièces typées ;
- **aucune version publiée depuis avril 2026** (dernier commit le 10 septembre), alors que ZenStack
  publie chaque semaine ;
- envoie des statistiques d'usage par défaut (désactivé dans la PoC).
Alternative non testée : `@zenstackhq/tanstack-query` (même version 3.9.7), des fonctions d'accès
**générées depuis le schéma, donc typées**, plus nos propres petites pièces (menu, « masquer si
interdit » : ~20 lignes chacune).

**4. Dépendance à des tiers → risque modéré, connu.**

| | ZenStack | Refine | Clerk |
|---|---|---|---|
| Activité | très active (41 versions en 2026, commit aujourd'hui) | ralentie (0 version depuis avril) | très active |
| Taille | petite (2,9 k étoiles, 42 k téléchargements/semaine) | grande (35,7 k étoiles, 274 k/semaine) | entreprise |
| Licence | MIT | MIT | service payant au-delà du gratuit |

Atténuation : versions figées dans le code livré ; la matrice reste la nôtre, la couche écran est
remplaçable sans toucher aux règles.

**5. Versions actuelles → beaucoup d'API ont changé depuis 2024.** Next 16 renomme `middleware`
en `proxy.ts` ; Clerk v7 remplace `SignedIn/SignedOut` par `<Show>` ; Refine v5 change la forme de
ses résultats ; ZenStack v3 retire l'API « puis-je ? ». Conséquence : **chaque pièce doit être
épinglée à une version et retestée à chaque montée de version** — les tests par rôle servent à ça.

## 3. Ce que la PoC a appris en plus

- **Les tests par rôle attrapent ce que les tests serveur ne voient pas.** Le premier passage
  Playwright a montré que « Mon profil » manquait au menu de l'adhérente : je demandais le droit
  « lister » alors qu'un profil (fiche unique) se « consulte ». Le serveur était juste, l'écran
  faux. Le menu doit se dériver de la **nature** de la fiche (ce que fait déjà `derive_nav`).
- **Défense en profondeur confirmée** : l'écran masque (affordance honnête), le serveur refuse
  (sécurité). Les deux couches lisent la même matrice.
- **Messages d'erreur trompeurs** : quand l'adhérente tente d'accepter sa propre demande, ZenStack
  répond « introuvable » (404) et non « interdit » (403). Sûr, mais à traduire pour l'utilisateur.
- **Rôle lu chez Clerk à chaque requête** : un appel à Clerk par requête. En production, mettre le
  rôle dans le jeton de session (réglage Clerk) pour supprimer cet appel.
- **Taille** : 3 fiches, schéma de 73 lignes dont ~20 de règles ; ~600 lignes d'app au total.
- **Tests Clerk faciles** : `@clerk/testing` connecte un compte de test en une ligne.

## 4. Pas testé (limites de la PoC)

Habillage shadcn/ui ; invitation Clerk d'un bibliothécaire (rôle posé par script) ; recherche et
pagination sur beaucoup de données ; coût des règles sur les performances ; évolution du schéma
par migrations (seulement `db push`) ; mise en ligne.

## 5. Recommandation

- **ZenStack v3 : retenu.** C'est le cœur du modèle de sécurité, et la traduction matrice → règles
  est mécanique, testable, sans IA.
- **La matrice reste la source unique** : l'usine génère les règles ET le tableau de l'écran.
- **Couche écran : pas encore tranchée.** Refine marche, mais apporte peu, n'est pas typé et
  ralentit. Avant de construire le catalogue de pièces dessus, un **essai comparatif court** :
  refaire les mêmes 3 écrans avec les fonctions typées de ZenStack, puis comparer (lignes, typage,
  confort). Le choix de la couche écran engage toutes les pièces : il vaut une demi-journée.

## Concepts utilisés

- **Règle « post-update »** : règle vérifiée *après* la modification, en comparant avec l'état
  d'avant (`before()`) ; si elle échoue, la modification est annulée. *Pourquoi* : c'est ce qui
  permet d'exprimer « seulement de demandé vers accepté ».
- **Transaction / annulation** : plusieurs écritures traitées comme une seule ; en cas de refus,
  rien n'est écrit. *Pourquoi* : pas de donnée à moitié modifiée.
- **IDOR** (accès par identifiant deviné) : demander l'emprunt de quelqu'un d'autre en tapant son
  identifiant. *Ici* : le serveur répond « rien », car la règle filtre chaque lecture.
- **Test de bout en bout (Playwright)** : un vrai navigateur piloté par un programme, qui clique
  comme un utilisateur. *Pourquoi* : vérifier ce que chaque rôle voit vraiment.
- **Épingler une version** : figer le numéro exact d'une dépendance. *Pourquoi* : une mise à jour
  silencieuse ne casse pas l'app livrée.

## Rejouer la démo

```
docker start temporal-postgresql
cd poc/mediatheque
npx next build && npx next start -p 3100     # puis http://localhost:3100
```
Comptes (mot de passe `Mediatheque-PoC-Oct2026!`, code de vérification éventuel `424242`) :
`adherent+clerk_test@example.com` et `bibliothecaire+clerk_test@example.com`. Accès forcés :
`/essais`. Tests : `npx tsx --env-file=.env scripts/test-policies.ts` et `npx playwright test`.
