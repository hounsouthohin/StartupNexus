# Anatomie d'une app bien formée — référence universelle

> Ce document est LA cible. Il ne décrit pas la médiathèque : il décrit **ce qu'est une app
> de gestion bien construite**, pour tout type de brief. La médiathèque n'en est qu'une
> instance (l'étalon de validation). L'architect et les compilateurs sont jugés contre CECI.
>
> Principe : **l'IA reconnaît (les natures, les intentions), le déterminisme complète (la
> mécanique).** L'IA ne devine pas des désirs ; elle ferme la logique de ce qui est demandé.

---

## 0. Loi fondatrice — l'affordance honnête

Une app = des **acteurs** qui déroulent un **processus** sur des **entités**, et qui en voient le
**reflet**. Tout élément visible est une **promesse** :

- un **lien** → mène à une destination réelle ET permise pour cet acteur ;
- un **bouton** → déclenche une action que l'acteur a le droit et le moyen de faire ;
- un **chiffre** → est calculé sur de vraies données ;
- une **action** → se termine et se **reflète** à l'écran.

**Règle unique : une affordance EXISTE ⇔ l'acteur a la CAPACITÉ ⇔ la DONNÉE existe.**
Sinon, elle n'apparaît pas. Une app « sans âme » = des affordances qui flottent (bouton qui
ne fait rien, lien qui 404, chiffre à 0, action sans effet). Tout le reste du document décline
cette loi.

---

## 1. Les TROIS natures d'entité (≠ un CRUD uniforme)

Le péché originel : traiter toute entité en list/create/detail/edit identique. Il y a **trois
natures**, à reconnaître dans le brief, chacune avec un comportement propre.

### A. PROFIL-SINGLETON — le « moi » de l'acteur
- **Définition** : une seule instance par personne ; elle EST la représentation de cet
  utilisateur dans le domaine.
- **Signaux** : « X gère **son** profil », l'entité porte les infos de la PERSONNE (nom, email,
  téléphone), possessif singulier, jamais « la liste des… » côté propriétaire.
- **Comportement compilé** :
  - PAS de liste, PAS de « nouveau », PAS de détail-par-id. **UNE** page « Mon profil ».
  - **Provisionnée automatiquement** (à l'inscription / première visite) — jamais via un
    formulaire « créer ». C'est une **clôture** (« gérer son profil » suppose qu'il existe).
  - `upsert` de la fiche du connecté ; possédée (`userId` unique) ; éditée par son seul
    propriétaire.
  - Nav : « Mon profil » (singulier). Le rôle privilégié (staff) n'en a PAS, sauf déclaré.
  - **Capacité future** (désir, pas clôture) : vue admin « liste des membres » → **miroir**.

### B. CATALOGUE PARTAGÉ — le référentiel commun
- **Définition** : entité partagée par tous, existant indépendamment de qui la crée.
- **Signaux** : « le catalogue », « les X que tout le monde consulte/réserve », public,
  pas de « mon/mes ».
- **Comportement compilé** :
  - **Global** (pas de `userId`). Lecture : liste + détail, **publique** (sans login) si le
    brief le dit.
  - **Gestion (créer/éditer/supprimer) UNIQUEMENT si le brief nomme un gestionnaire.**
    Sinon **LECTURE SEULE** : zéro bouton créer/éditer/supprimer, pour personne. (Le catalogue
    est alimenté hors app.)
  - Nav : une porte vers le catalogue.

### C. COLLECTION POSSÉDÉE (± workflow) — l'acte métier
- **Définition** : des enregistrements créés et possédés par un acteur, parfois soumis à un
  cycle de vie décidé par un autre.
- **Signaux** : « X **demande/crée** un Y », « X ne voit que **ses** Y », des états qui
  s'enchaînent, « seul Z peut faire évoluer l'état ».
- **Comportement compilé** :
  - Possédée (`userId` = l'initiateur). **Créée par l'INITIATEUR déclaré** ; les autres acteurs
    n'ont NI bouton NI page « créer ».
  - **FK-de-contexte = AUTO** : on ne choisit jamais « soi-même » ni son propre profil dans un
    formulaire (le champ est rempli depuis le contexte). On ne choisit que le **référentiel**
    (ex : quel ouvrage).
  - L'initiateur voit **les siens** ; le rôle privilégié voit **tout** (`getAllAsAdmin`) et peut
    **ouvrir chaque item** (`getByIdAsAdmin`) — sinon il voit la liste mais 404 sur le détail.
  - **Workflow** : état initial forcé ; transitions en **liste blanche** ; **décidées par le
    décideur seul** (garde serveur) ; l'écran de décision est **atteignable** par le décideur.
  - **Affordances d'action honnêtes** : éditer/supprimer/décider n'apparaissent QUE pour l'acteur
    qui en a la capacité réelle (owner pour ses champs libres tant que non verrouillé ; décideur
    pour la transition). Sinon, **pas de bouton** (ni bouton mort, ni bouton qui erreur).

---

## 2. Le DASHBOARD — hub différencié par rôle

- Le dashboard est une **page-mère**, pas une page-donnée : un **aperçu** (1 à 3 indicateurs
  pertinents POUR CET ACTEUR, **calculés**, jamais 0 en dur) + des **portes** (cartes/boutons)
  vers ses zones.
- **Différencié par rôle** : le dashboard de l'adhérent (« mes emprunts en cours » + portes vers
  *Catalogue*, *Mes emprunts*, *Mon profil*) ≠ celui du bibliothécaire (« emprunts à traiter » +
  portes vers *File des décisions*, *Catalogue*). Deux intentions, deux dashboards.
- **Jamais** le doublon d'une autre page.

---

## 3. Localisation — zéro nom technique visible

Aucun nom de modèle brut (anglais) ne doit apparaître à l'écran. **Tout** libellé — titres, nav,
boutons, noms d'entités, noms de champs, valeurs d'enum — est dans la **langue du brief**.
« Borrowing » visible = bug. La localisation est un **invariant**, pas un détail cosmétique.

---

## 4. Rôles / acteurs

- Un rôle = **accès privilégié dans le MÊME espace** de données (pas de multi-tenant).
- Le privilégié : **voit-tout** + **décide** ; n'est **pas** un membre (pas de profil, sauf
  déclaré). Le décideur d'une entité n'en est **pas** l'initiateur.
- **Attribution** : bootstrap par email (démo/1er admin) OU `publicMetadata.role` Clerk (prod).

---

## 5. Clôture vs désir — la règle de décision de l'architect

- **CLÔTURE** : la mécanique **impliquée par nécessité** par ce qui est demandé, sans quoi la
  demande est **incohérente** (profil provisionné, écran de décision atteignable, FK-de-contexte
  auto…). → l'architect la **complète automatiquement**.
- **DÉSIR** : une capacité qui n'est **pas nécessaire** au fonctionnement de ce qui est demandé
  (notifications, vue admin des membres, gestion du catalogue non demandée…). → l'architect
  **ne l'ajoute PAS** ; le **miroir** la remonte à l'humain (pré-interpréteur / client).
- **Test** : *le comportement demandé est-il incohérent sans ça ?* Oui → clôture. Non → désir.
  **Doute → désir** (on surface, on ne devine pas).

---

## INSTANCIATION — la médiathèque (l'étalon)

### Schéma & natures
| Entité | Nature | Conséquences |
|---|---|---|
| **Ouvrage** (titre, auteur, résumé, genre, année) | **B — catalogue partagé** | global, public en lecture (liste + fiche), **lecture seule** (personne n'est déclaré pour le gérer) |
| **Adhérent** (nom, email, téléphone, userId) | **A — profil-singleton** | « Mon profil », provisionné à l'inscription, édité par le seul adhérent ; pas de liste ; le bibliothécaire n'en a pas |
| **Emprunt** (dateDemande, état, bookId→Ouvrage, memberId→Adhérent auto, userId) | **C — collection possédée + workflow** | créé par l'adhérent (choisit l'ouvrage ; memberId auto) ; workflow décidé par le bibliothécaire |

### Workflow de l'emprunt
`demandé → (accepté | refusé)` ; `accepté → rendu` ; `refusé`, `rendu` = terminaux.
Transitions **décidées par le bibliothécaire seul** ; l'adhérent **demande et suit** (lecture).

### Les deux dashboards
- **Adhérent** : « mes emprunts en cours » ; portes → *Catalogue*, *Mes emprunts*, *Mon profil*.
- **Bibliothécaire** : « emprunts en attente de décision » ; portes → *Emprunts à traiter*, *Catalogue*.

### Nav par acteur
- **Visiteur** : Accueil · Ouvrages · Connexion.
- **Adhérent** : Ouvrages · Mes emprunts · Mon profil.
- **Bibliothécaire** : Emprunts (à décider) · Ouvrages.

### Matrice d'accès
| Action | Visiteur | Adhérent | Bibliothécaire |
|---|:---:|:---:|:---:|
| Parcourir le catalogue (liste + fiche) | ✅ | ✅ | ✅ |
| Gérer **son** profil | — | ✅ | — |
| **Demander** un emprunt (choisir 1 ouvrage) | — | ✅ | ❌ |
| Voir les emprunts | — | les siens | tous |
| **Décider** (accepter/refuser/rendu) | — | ❌ | ✅ |
| Éditer / supprimer un emprunt | — | ❌ | ❌ |
| Gérer le catalogue | — | ❌ | ❌ *(désir → miroir)* |

### Désirs surfacés par le miroir (non construits — décision humaine)
- Vue admin « liste des adhérents » (pattern quasi-universel, mais pas dans le brief, pas de
  mécanisme startup).
- Gestion du catalogue (ajouter/éditer un ouvrage) par un gestionnaire.

---

**« App bien formée » = conforme à ce document.** L'étape suivante : mapper CECI en (a) ce que
l'architect doit *reconnaître et déclarer*, (b) quels compilateurs doivent le *produire*.
