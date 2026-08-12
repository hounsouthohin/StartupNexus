# Détecteur amont — les 7 axes d'intention & la carte des cases

> **Principe** (issu des recherches) : ne pas énumérer les *types d'apps* (infinis) mais les
> **axes d'intention** (peu nombreux, fermés). Toute phrase de brief atterrit sur l'un d'eux.
> **Une case manque quand une phrase tombe sur un axe dépourvu de nœud** (ou à nœud trop mince).
>
> **L'instrument** : pour chaque phrase du brief, l'architecte rend soit une **référence de
> nœud**, soit **« non-mappé »**. La liste des non-mappés = le **détecteur de cases manquantes**,
> en amont, sans clic. C'est notre ligne 🔴 « une case manque → rien ne le voit », comblée.

---

## 1. Les 7 axes, et notre couverture RÉELLE (nœuds existants)

| Axe | Question | Nœud(s) dans notre déclaration | Couverture |
|---|---|---|---|
| **1. Acteurs** | qui existe | `RoleDeclaration.roles`, `privileged_role` | 🟢 solide |
| **2. Entités + natures** | quoi existe, de quelle nature | `models` (structure) ; natures : `is_global` (catalogue) ✓, collection+workflow ✓ ; **profil-singleton ❌**, classification explicite des natures ❌ | 🟡 **mince** |
| **3. Permissions** | qui peut faire quoi à quoi, sous quelle condition | `role_gated_actions`, `initiator` (S1), owner (crud), `admin_scoped_views` (K2), gardes serveur | 🟢 solide |
| **4. États** | ce qui change dans le temps | `status_flows` (transitions, locked_states, state_fields) | 🟢 solide |
| **5. Agrégats** | ce qui est calculé | `KPIDeclaration`, `FilteredListDeclaration` existent ; **calcul temporel (mois courant, groupement) ❌** | 🟡 **mince** |
| **6. Navigation** | ce qui est vu, et par qui | `surface` par acteur (S2), `pages` ; **dashboard = hub différencié ❌** | 🟡 **mince** |
| **7. Libellés** | ce qui est dit | `title_plurals`, `ui_labels`, `enum_value_labels` ; **fuites (noms techniques visibles) ❌** | 🟡 **mince** |

**Lecture immédiate** : on a un nœud sur **les 7 axes** — mais **4 sont minces** (natures, agrégats
calculés, dashboard-hub, libellés complets). *Ces 4 nœuds minces sont exactement là où la
médiathèque a cassé.* Le détecteur, appliqué à notre propre déclaration, **prédit déjà** les
défauts — sans qu'un humain n'ouvre l'app.

---

## 2. Application au brief médiathèque — phrase par phrase

Chaque phrase → un axe → un nœud (🟢 couvert) ou un non-mappé/mince (🔴 = la case à faire).

| Phrase du brief | Axe | Nœud | Verdict |
|---|---|---|---|
| « visiteurs, sans se connecter, parcourent le catalogue public » | 2 + 3 | catalogue global + auth publique | 🟢 |
| « chaque ouvrage a titre, auteur, résumé, genre, année » | 2 | model + champs + enum | 🟢 |
| « un adhérent **gère son profil** » | 2 (nature) | **profil-singleton** | 🔴 **absent** → *404 du profil* |
| « le catalogue… **personne n'est déclaré pour le gérer** » | 2 (nature) | **catalogue lecture-seule** | 🔴 **mince** → *« gérer ouvrages » fantôme* |
| « demande à emprunter un ouvrage » | 3 | `initiator` (adhérent crée) | 🟢 (fait S1) |
| « demandé → accepté|refusé ; accepté → rendu » | 4 | `status_flows` | 🟢 |
| « seul le bibliothécaire décide » | 3 | `role_gated_actions` (décideur) | 🟢 |
| « un adhérent ne voit que **ses** emprunts ; le bibliothécaire **tous** » | 3 + 6 | owner + `admin_scoped` + `surface` | 🟢 (fait K2/S2) |
| « choisir un **Member** dans le formulaire » (implicite) | 3 (FK) | **FK-de-contexte auto** | 🔴 **absent** → *champ « Member » absurde* |
| « tableau de bord : chiffre d'affaires **du mois**, nb en attente, impayés » | 5 | **agrégat temporel calculé** | 🔴 **mince** → *compteurs à 0* |
| « tableau de bord » (structure) | 6 | **dashboard = hub différencié** | 🔴 **absent** → *dashboards identiques* |
| « interface claire, chaleureuse » + « Borrowing » visible | 7 | libellés complets | 🔴 **mince** → *nom technique en anglais* |

---

## 3. Ce que ça DÉMONTRE (la thèse, prouvée sans clic)

Les **6 défauts** trouvés par test humain la semaine dernière —
1) profil 404, 2) « gérer ouvrages » fantôme, 3) champ « Member », 4) compteurs à 0,
5) dashboards identiques, 6) « Borrowing » en anglais —
**tombent EXACTEMENT sur les nœuds marqués 🔴** ci-dessus.

> **Le détecteur amont, appliqué à un seul brief, aurait sorti la liste des 6 bugs AVANT
> qu'on n'ouvre l'app.** C'est « en un jour, sur papier, ce que les tests humains ont mis des
> jours à révéler ». La thèse tient.

---

## 4. La carte des cases à faire (dérivée, plus réactive)

Priorité = les nœuds 🔴, dans l'ordre où les briefs les réclament :

- **CASE natures d'entité** (axe 2) : classer chaque entité en profil-singleton /
  catalogue-lecture-seule / collection-workflow. → règle nos bugs 1, 2 (et cadre S3a/S3b).
- **CASE FK-de-contexte** (axe 3) : marquer une FK « auto-remplie » (jamais un champ à choisir). → bug 3.
- **CASE agrégat calculé** (axe 5) : op + champ + filtre + **fenêtre temporelle** + groupement. → bug 4.
- **CASE dashboard-hub différencié** (axe 6) : aperçu calculé + portes, par acteur. → bug 5.
- **CASE libellés complets** (axe 7) : invariant « zéro nom technique visible ». → bug 6.

Chaque case livrera ses **deux moitiés** : le **compilateur** (code) **et** son **ORACLE**
(test dérivé de la déclaration, lancé contre l'app qui tourne).

---

## 5. Test des « 7 axes » sur des briefs VARIÉS — résultat

On a mappé 3 types différents pour voir si des phrases tombent **hors** des 7 axes.

**E-commerce léger** (produits, panier, commande, **paiement**, **e-mail de confirmation**) :
- produits→2 · panier/commande→2+4 · « seul l'acheteur voit ses commandes »→3 : 🟢 mappés.
- **« paiement »** → aucun des 7. **« e-mail de confirmation »** → aucun des 7. 🔴 **hors-axes.**

**Réservation / booking** (ressources, créneaux, **conflit de créneaux**, **rappel avant l'événement**) :
- ressources→2 · réservation→2+4 : 🟢.
- **« deux réservations ne peuvent se chevaucher »** → condition inter-enregistrements : partiellement
  axe 3, mais pas un simple droit → **contrainte métier** mal logée.
- **« rappel avant l'événement »** → action **déclenchée dans le temps** → aucun des 7. 🔴 **hors-axes.**

**Réseau social léger** (profils, posts, follows, feed, likes) : tout tombe sur 2/5/6. 🟢.

### Verdict : « sept » n'est PAS fermé — il en manque (au moins) deux

Le détecteur a fait **son** travail : en mappant, il a révélé des phrases qui ne tombent nulle part.
Deux axes candidats émergent, récurrents sur des types courants :

- **AXE 8 — Effets externes / intégrations** : e-mail, paiement, webhooks, notifications. (« ce qui
  SORT de l'app vers le monde ».) Aujourd'hui : **aucun nœud** → ces demandes iront toujours dans
  `unsupported[]` (miroir), jamais compilées. Décision clôture/désir à trancher par type.
- **AXE 9 — Temporel / déclenché** : rappels, tâches planifiées, récurrences, expiration. (« ce qui
  arrive SANS qu'un acteur clique ».) Aucun nœud.
- **Nuance sur l'axe 3** : les **contraintes inter-enregistrements** (chevauchement, unicité métier)
  débordent le simple « qui a le droit ». À clarifier : sous-nœud de l'axe 3, ou axe « invariants ».

> **C'est exactement le résultat espéré :** on ne SUPPOSE plus le modèle, on le **teste**, et le
> test l'agrandit de façon dérivée (7 → ~9).

---

## 6. Stabilisation — 6 briefs de plus (types variés)

Objectif : voir si tout tombe sur la liste, ou si d'autres axes émergent. On note par brief ce
qui **sort** des axes connus ou ce qui est **ambigu**.

| Brief (type) | Ce qui a mappé sans peine | Nouveau / hors-axe / ambigu |
|---|---|---|
| **Blog/CMS** (articles, brouillon→publié, tags, commentaires, SEO) | 2, 3, 4, 6, 7 | « image de couverture » = **média** (nature de champ + upload→8) · « filtrer par tag » = **recherche/filtre** (sous-nœud de 6) · « SEO » = méta (7) |
| **Gestion de projet** (projets/tâches, statut, échéance, assignation, retard) | 2, 3, 4 | « échéance / en retard » → **9 (temporel calculé)** · « assignée à un membre » = relation vers un **acteur** (2+3) |
| **Facturation freelance** (clients, factures+lignes, total, PDF, e-mail, CA du mois) | 2, 4 | « total » → 5 · « PDF » + « e-mail » → **8** · « en retard / CA du mois » → **9** (fenêtre temps) |
| **E-learning** (cours/leçons, inscription, progression, quiz, certificat) | 2, 3 | « progression » → 5 · « certificat si quiz réussi » → **8** (génère un doc) **déclenché par une condition** (3) |
| **Support/ticketing** (tickets, statut, agent assigné, temps de réponse, notif) | 2, 3, 4 | « temps de réponse » → 5+**9** · « notification à chaque changement de statut » → **8 déclenché par une transition (4)** |
| **Événementiel** (événements, capacité, inscription tant qu'il reste des places, rappel la veille, check-in) | 2, 3, 4 | « **capacité max / tant qu'il reste des places** » = **contrainte inter-enregistrements** · « rappel la veille » → **9+8** |

### Résultat : la liste se STABILISE à **9 axes** (rien de nouveau au-delà)

Sur 9 briefs au total (médiathèque + 8), **tout finit par tomber sur ces 9** — les deux ajouts
(8, 9) se **confirment fortement** (chacun dans 4+ briefs), et **aucun 10ᵉ axe** n'a émergé.

1. **Acteurs** — qui existe
2. **Entités + natures** — quoi existe, de quelle nature *(inclut les natures de champ : enum, date, montant, **média**)*
3. **Permissions & conditions** — qui peut faire quoi, sous quelle condition *(inclut les **contraintes inter-enregistrements** : capacité, chevauchement, unicité — un check à travers les lignes, pas un simple droit)*
4. **États** — cycle de vie / transitions
5. **Agrégats** — ce qui est calculé (totaux, comptes, progression)
6. **Navigation** — ce qui est vu, par qui *(inclut **filtres / recherche** : comment on trouve ce qu'on voit)*
7. **Libellés** — ce qui est dit (labels, méta/SEO)
8. **Effets externes** — ce qui SORT vers le monde (e-mail, PDF/export, notification, génération de doc, paiement) — **NOUVEAU**
9. **Temporel / déclenché** — ce qui arrive sans clic (échéance, retard, rappel, SLA, récurrence, expiration) — **NOUVEAU**

### Nuances importantes (pour la conception, pas pour la liste)

- **Axes non-orthogonaux, mais couvrants.** 5 et 9 se chevauchent (« en retard » = calculé **et**
  temporel). 8 se **compose** souvent avec 4 (« notification à chaque changement de statut »,
  « certificat si quiz réussi » = **effet déclenché par une transition/condition**). Ce n'est pas
  un défaut : pour un **détecteur**, la **complétude** (tout se mappe) prime sur l'orthogonalité.
- **Motifs récurrents à compiler** (compositions, pas nouveaux axes) : *effet-sur-transition*
  (4→8), *champ-média* (2+8), *contrainte-inter-lignes* (3), *filtre/recherche* (6).

### Où on en est sur la couverture (les 9 axes × nos nœuds)

- Solides : **1, 3, 4** · Minces : **2 (natures), 5 (temporel), 6 (dashboard-hub), 7 (fuites)** ·
  **Absents : 8 (effets externes), 9 (temporel/déclenché)** — aujourd'hui ces deux familles vont
  toujours dans `unsupported[]` (le miroir les avoue, aucun compilateur ne les produit).

> **La liste est stable et complète (9). Elle peut devenir l'ossature de l'architecte :** pour
> chaque phrase du brief, l'architecte rend un nœud sur l'un des 9, ou « non-mappé ». La colonne
> « non-mappé » devient, automatiquement, la file des cases à construire — par ordre de demande réelle.
