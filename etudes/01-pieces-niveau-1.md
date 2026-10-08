# Étude 01 — Les pièces du niveau 1 : les construire, ou partir de l'existant ?

*5 octobre 2026 — étude sans code. Première brique de la documentation de la nouvelle conception
(usine d'assemblage : comprendre → contrôler → faire valider → assembler des pièces → vérifier).*

## 1. La question

Pour le niveau 1 (« Gérer » : fiches, catalogues, demandes à états, 1 à 3 rôles, chacun ne voit et
ne fait que ce qu'il doit), de quelles pièces avons-nous besoin, et une bibliothèque existante
peut-elle les fournir sur notre stack (Next.js + Prisma + Clerk) ?

## 2. Inventaire des pièces du niveau 1

**Pièces d'écran**

| Pièce | Rôle | Ce qu'elle lit dans la notice |
|---|---|---|
| Coquille + menu par rôle | cadre de l'app, menu différent selon qui est connecté | rôles, ce que chacun voit |
| Liste de fiches | tableau ou cartes, recherche, filtre par état, pagination | champs, libellés, droits « voir » |
| Fiche détail | tous les champs, liens affichés (« voir au travers de »), badge d'état | champs, liens, droits |
| Formulaire | créer / modifier ; champs typés ; liens choisis ou remplis automatiquement | champs, droits « créer / modifier » |
| Bloc de décision | boutons d'évolution selon l'acteur et l'état ; champs à saisir (motif d'un refus) | circuit, qui fait chaque étape |
| Enfants dans le parent | liste + ajout dans la fiche du parent (lignes, participants) | relation parent → enfant |
| Mon profil | la fiche unique de la personne, créée automatiquement | nature « profil » |
| Tableau de bord par rôle | « à traiter », « mes … en cours », portes | tableau « qui fait quoi » |
| Pages publiques | catalogue et fiche visibles sans compte (publiés seulement si brouillons) | visiteur, publication |
| Équipe | inviter quelqu'un avec un rôle (invitation Clerk) | chemins d'entrée des acteurs |

**Pièces de données (côté serveur)** : règles d'accès par rôle appliquées à chaque lecture et
écriture ; actions génériques (créer, modifier, supprimer, faire évoluer l'état) avec validation des
entrées ; structure de la base fabriquée depuis la notice ; données de démonstration.

**Types de champs à couvrir** : texte, texte long, nombre, montant, date/heure, oui/non, liste fixe
(valeurs numériques comprises — panne d'un vrai brief), lien vers une fiche, liens multiples,
e-mail, téléphone, adresse web.

**Vérification** : tests par rôle sur l'app assemblée, dérivés du tableau (« le client tente
d'accepter → refusé »).

*Une bonne partie existe déjà dans l'usine actuelle sous forme de gabarits (liste, détail,
formulaire, enfants) : leur savoir sera repris, pas jeté.*

## 3. Les candidats

| | Refine | React-Admin | Wasp | ZenStack |
|---|---|---|---|---|
| Ce que c'est | cadre « sans habillage » pour apps de gestion : listes, formulaires, droits | même famille, plus ancien | langage qui décrit toute l'app et la produit | extension du schéma Prisma avec règles d'accès |
| Next.js | ✅ App Router pris en charge | ⚠️ pensé pour une app 100 % navigateur | ❌ son propre serveur (Node), pas Next.js | ✅ App Router |
| Clerk | ✅ via son « authProvider » | ✅ | ❌ sa propre authentification | ✅ intégration officielle documentée |
| Droits par rôle | ✅ gratuit (`accessControlProvider`, `CanAccess` : masque boutons et menus) | ❌ **payant** (version Entreprise) | ✅ | ✅ **refus par défaut**, appliqué à chaque requête |
| Habillage | ✅ intégration shadcn/ui officielle (déjà notre bibliothèque visuelle) | Material UI | le sien | — (couche données) |
| Licence | libre (MIT) | libre, sauf droits par rôle | libre | libre |
| Verdict | **retenu pour les écrans** | écarté (droits payants, autre habillage) | écarté comme base (pas notre stack) ; inspirant | **retenu pour les données et les droits** |

**Mage** (générateur IA construit sur Wasp, 2023) : GPT écrivait tout le code de l'app depuis une
courte description ; erreurs fréquentes, lent, cher ; projet abandonné. C'est l'approche que nous
quittons — et une confirmation de notre choix : l'IA comprend, un programme assemble.

## 4. Recommandation

**Ne pas construire le catalogue de zéro. Assembler deux briques libres, éprouvées, compatibles
avec notre stack :**

```
   notice + tableau « qui fait quoi »   ← NOTRE valeur (l'IA comprend, le client valide)
          │                    │
          ▼                    ▼
   règles ZenStack         ressources Refine
   (dans le schéma)        (listes, fiches, formulaires)
          │                    │
   refus côté serveur ◄──── même vérification ────► boutons et menus masqués
   à CHAQUE requête          (API « check »)          à l'écran
```

- **ZenStack** porte les règles d'accès : notre tableau « qui fait quoi » se traduit en règles
  `@@allow` dans le schéma. Tout est refusé par défaut (notre doctrine du moindre privilège) et la
  règle s'applique à chaque requête, quoi que fasse l'écran. Il génère aussi les accès aux données
  (une API par modèle) déjà protégés.
- **Refine** porte les écrans, habillés avec shadcn/ui. Son contrôle des droits interroge la même
  vérification ZenStack : **une seule source de règles pour deux couches** (défense en profondeur
  + affordance honnête). Cette combinaison est documentée par ZenStack (article de mai 2024).
- **Nous construisons** : la notice, le tableau, leurs traductions (tableau → règles ZenStack,
  notice → ressources Refine), les pièces qui nous sont propres (bloc de décision, mon profil,
  tableau de bord par rôle, équipe), l'assembleur et les tests par rôle.

## 5. Ce que nous ne savons pas encore (honnêtement)

1. **ZenStack version 2 ou 3 ?** La v3 remplace le moteur Prisma par le sien (même schéma, mêmes
   requêtes, données inchangées) ; la v2 s'appuie sur Prisma. Choix à faire en connaissance de cause.
2. **Les circuits d'états** (« seul le bibliothécaire passe de demandé à accepté ») s'expriment-ils
   proprement en règles ZenStack ? À vérifier par l'essai.
3. **Refine dans Next.js** fonctionne surtout côté navigateur, en appelant une API : c'est un
   changement par rapport aux actions serveur de l'usine actuelle. Maturité réelle à vérifier.
4. **Dépendance à deux projets tiers** (ZenStack est une petite équipe). Atténuation : le code est
   livré chez le client, versions figées ; on peut les remplacer si besoin, la notice restant la nôtre.
5. L'article qui combine les deux date de 2024 (ZenStack 2). À revérifier sur les versions actuelles.

## 6. Étape suivante proposée : une preuve de concept

Un essai court et jetable : **assembler à la main** l'app de la médiathèque avec Refine + ZenStack +
Clerk, avec les règles de sa matrice de référence. Il tranche les 5 inconnues avant d'écrire
l'architecture.

Ce qu'on vérifiera : (1) le serveur refuse un accès interdit, même forcé ; (2) boutons et menus
différents pour l'adhérent et le bibliothécaire ; (3) le circuit d'états respecté ; (4) « mon
profil » ; (5) le catalogue public. Démo : connexion en adhérent puis en bibliothécaire.

## Concepts utilisés dans cette étude

- **ORM** : outil pour parler à la base de données en code typé plutôt qu'en SQL brut (Prisma,
  ZenStack). *Pourquoi* : moins d'erreurs, et le compilateur vérifie les requêtes.
- **Règle d'accès au niveau des données** : la règle est vérifiée à chaque requête, au plus près
  de la base. *Pourquoi* : même si un écran oublie une vérification, la donnée reste protégée.
- **Cadre « sans habillage »** (headless) : fournit la logique (listes, formulaires, droits) sans
  imposer l'apparence ; on habille avec shadcn/ui. *Pourquoi* : garder notre identité visuelle.
- **Data provider** : l'adaptateur qui relie Refine à une source de données (ici l'API générée par
  ZenStack). *Pourquoi* : Refine ne sait rien de notre base ; l'adaptateur fait le lien.
- **Preuve de concept** : petit essai jetable pour vérifier qu'une idée tient avant d'investir.

## Sources

- Refine — Next.js : https://refine.dev/core/docs/routing/integrations/next-js/
- Refine — Access Control Provider : https://refine.dev/core/docs/authorization/access-control-provider/
- Refine — shadcn/ui : https://refine.dev/blog/shadcn-ui/
- React-Admin — RBAC (Entreprise) : https://marmelab.com/react-admin/AuthRBAC.html
- ZenStack — Clerk : https://zenstack.dev/docs/quick-start/authentication/clerk
- ZenStack — Next.js App Router (v2) : https://zenstack.dev/docs/2.x/quick-start/nextjs-app-router
- ZenStack v3 : https://zenstack.dev/blog/prisma-alternative
- Refine + ZenStack (mai 2024) : https://zenstack.dev/blog/refine-dev-backend
- Wasp : https://github.com/wasp-lang/wasp — Mage : https://wasp.sh/blog/2023/07/10/gpt-web-app-generator
