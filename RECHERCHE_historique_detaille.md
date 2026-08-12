# Historique détaillé de l'usine — en réponse à ta première analyse

> **À l'IA de recherche.** Ta première conclusion était **fine sur le diagnostic de fond**
> (le brief ne contient pas l'app ; régénération ≠ déterminisme ; le client est l'humain
> irréductible ; le piège des 20 %). Mais **plusieurs de tes prémisses factuelles ne
> correspondent pas à l'histoire réelle** — parce qu'on t'avait donné un résumé, pas les faits
> datés. Voici l'historique vérifié (roadmap + journal de bord + code). Il **contredit
> précisément** deux points sur lesquels reposait ta prescription. Ré-évalue avec ça.

---

## PARTIE 1 — La chronologie réelle (datée, vérifiée)

L'usine a **~5 mois d'itérations datées** (Fév → Août 2026), versions v2.0 → v4.x.

- **Fév–Mai 2026 (v2.0 → v3.2)** : socle du pipeline (architecte → génération → build → deploy).
  **Un artefact structuré (ProjectSpec / IR) a existé dès le début** : l'architecte a *toujours*
  produit une spécification formelle. **Il n'y a jamais eu d'ère « agents en roue libre sans
  artefact partagé ».**
- **Mai–Juin (v3.3 → v3.6)** : le design/front est d'abord confié à un **FrontendActivity 3
  couches**, puis planifié comme **FrontendAgent ReAct** (v3.7, 6 Juin).
- **18 Juin (v3.8)** : le **FrontendAgent est ANNULÉ** — le design est **intégré dans le pipeline
  déterministe**. ⚠️ **C'est le seul « retrait d'agent » de l'histoire** : *un* agent (le front),
  remplacé par des générateurs. **L'architecte LLM et l'executor LLM sont restés.** L'usine a
  **toujours été hybride** — jamais « on supprime les agents ».
- **6 Juil (v3.9)** : priorité **expansion** ; **3/3 BUILD_SUCCESS** sur des types différents
  (writer-pad, freelance-tracker, sprint-board). L'usine sait produire des apps qui **compilent**
  pour plusieurs types.
- **16 Juil (v4.0 — « relecture terrain »)** : **la découverte centrale.** (Voir Partie 2.)
- **23 Juil** : « état consolidé ». Constat noir sur blanc : **« On n'a jamais fait tourner une
  seule app. Jamais cliqué un bouton. Zéro app livrée. »** (PRINCIPE 6 déclaré **VIOLÉ**.) La
  moitié GAUCHE (générer) marche en ~95 s ; la moitié DROITE (preview + deploy) **n'existe pas
  encore**.
- **25–26 Juil → 1 Août (cette période)** : construction de la **preview** (l'app tourne enfin,
  URL live) → **premiers tests humains** → découverte des incohérences « app sans âme » →
  travail « sémantique » (rôles, natures d'entités, affordance honnête).

**À retenir : l'usine n'a commencé à être *cliquée par un humain* que très récemment.** Tout le
reste (build vert, review 100/100, coverage 1.0) était mesuré **sans qu'un humain n'ouvre l'app.**

---

## PARTIE 2 — Tes prémisses confrontées aux faits

### ❌ Prémisse « pas d'artefact partagé »
**Faux pour notre histoire.** L'AST (ProjectSpec, puis EnrichedSpec) a existé **dès les premières
versions**. Le problème n'a **jamais** été l'*absence* d'artefact — mais que l'artefact était
**INCOMPLET** : il lui **manquait des cases** (des nœuds typés) pour porter certaines intentions.
C'est notre découverte fondatrice, la **« loi du contenant »** (16 Juil) :

> **Toute intention client sans structure pour la porter s'évapore — quelle que soit
> l'intelligence du LLM.**

**Preuve datée (run `notes-frais`, 16 Juil).** Brief : *« on ne doit pas pouvoir rembourser une
note non approuvée »*. L'architecte a **parfaitement compris** (5 états extraits dans le bon
ordre depuis une prose qui ne les listait pas, `@default(draft)`, `rejectionReason` déduit de
« refusée avec un motif »). Mais **aucun nœud de l'AST ne pouvait porter l'ordre des états ni les
sauts interdits** → le savoir est **tombé par terre** ; la phrase du client est devenue… des
couleurs de badge. On a créé la case (`StatusFlowDeclaration`) → l'architecte l'a **remplie
parfaitement, du premier coup, sans un seul réglage de prompt**, et **répété 3 fois le même jour**.
**L'intelligence était là depuis le début. Ce qui manquait, c'était le contenant.**

→ Conséquence : *l'intelligence n'a jamais été le goulot d'étranglement, et un « artefact
partagé » l'était encore moins puisqu'il existait.* Le goulot, c'est **l'ensemble des cases**.

### ❌ Prémisse « pas de juges non-humains »
**Faux, et c'est le point qui doit faire bouger ton verdict.** Des juges non-humains ont existé
**tout du long** : `tsc`, `next build`, `prisma validate`, un capteur de couverture, un capteur
de qualité, **et** un reviewer LLM. **Deux modes d'échec réels, tous les deux AVEC juges présents :**

1. **`notes-frais` (16 Juil)** : `BUILD ✅ · spec_coverage 1.0 · requirements 6/6 ·
   quality_violations 0 · review COHERENT 100/100` — **sur une app cassée** (créer une note déjà
   « Remboursée »). → **TOUS les juges ont validé une app absurde.** Le juge n'était pas *absent* ;
   il était **aveugle au sens.**
2. **Post-« Option A » (avant)** : `3/3 BUILD_FAILED`, **boucle TS2345 stagnante** — avec `tsc`
   présent. → Le juge était là ; **l'agent bouclait quand même** (pas de convergence).

**Le mur, énoncé précisément :** un compilateur (`tsc`) juge la **compilabilité**, jamais le
**sens**. Le seul juge capable de juger le sens serait **une IA** — et notre IA-juge (le reviewer)
**MENT** : *« il inspecte la sortie d'un compilateur, correcte par construction ; il n'a rien de
réel à trouver, alors il fabrique du réconfort — COHERENT 100/100. »* Donc :

> **« Ajouter des juges non-humains » ne peut pas atteindre la sémantique** : les juges non-humains
> disponibles (compilateurs) ne jugent que la forme, et le juge du sens (LLM) est **structurellement
> peu fiable** (il rubber-stampe). C'est exactement le problème que le déterminisme contourne, pas
> celui qu'il ignore.

### ❌ Prémisse « vous avez conclu qu'il fallait supprimer les agents »
**Épouvantail** (involontaire, faute de contexte). On a supprimé **un** agent (le FrontendAgent,
18 Juin). L'architecte LLM et l'executor LLM sont **toujours là** : *« un compilateur doit rester
petit mais jamais disparaître — c'est lui qui fait que l'usine RÉPOND à n'importe quel brief. »*
Ton propre « cadre hybride » recommandé est **plus proche de ce qu'on a** que tu ne le penses.

### ✅ Ce que tu vois juste (et qu'on n'avait pas nommé aussi bien)
- **Régénération ≠ déterminisme.** Concorde à 100 % avec notre **idéal #2** : *« la déclaration
  est le produit — corrige 1× → recompile tout le parc. »* C'est de la **régénération**, et tu as
  raison qu'on l'avait **fusionnée** avec le déterminisme dans notre tête. Distinction précieuse.
- **Le client est l'humain irréductible.** Concorde avec notre **idéal #4** (*machine juge le
  technique, humain juge le sens*) et la règle **clôture vs désir** qu'on a formalisée depuis.
- **Le piège des 20 % / « sors l'URL ».** **On le savait déjà** — et c'est le plus gênant : la
  roadmap du 23 Juil déclare **PRINCIPE 6 VIOLÉ** (« complétion utilisable avant complexité ») et
  **promeut la Scène** (PRINCIPE 8 : *« la Scène est le seul instrument qui ne peut pas mentir »*).
  Ta conclusion **concorde avec une vérité déjà écrite mais pas encore agie.** Utile comme rappel,
  pas comme révélation.

### ⚠️ Ce que tu dois ré-examiner : le « chemin structurel »
Ta critique **« les générateurs ne composent pas → tu gonfles à l'infini, un compilateur par
cas »** a **du mordant** — on empile effectivement des compilateurs (types A/D/I/K, puis S1…S5).
On te l'accorde. **Mais ta solution** (« déplace les invariants côté vérificateurs, laisse des
agents régénérer sous contrainte, et le rêve d'autonomie redevient atteignable ») **doit
maintenant affronter les deux faits ci-dessus** :

- Le **vérificateur du sens** est une **IA qui ment** (COHERENT 100/100). Déplacer les invariants
  « côté juges » suppose un juge du sens **fiable** — or c'est précisément ce qu'on n'a **jamais**
  eu. Comment ton chemin structurel obtient-il un juge sémantique fiable ?
- **« Agents qui régénèrent sous contrainte »** suppose une **convergence** fiable. Notre histoire
  montre l'inverse (boucle TS2345, avec juge présent). Qu'est-ce qui garantit la convergence là où
  elle a échoué ?
- Le déterminisme nous donne la **reproductibilité** — la garantie même qu'on voudrait **vendre**.
  Ton chemin l'échange contre la composabilité. **Quel est le vrai solde** de cet échange pour une
  entreprise dont la valeur = des garanties ?

---

## PARTIE 3 — Ce que la startup a DÉJÀ identifié comme manquant (sa propre carte)

Fait important : l'usine a **déjà nommé** ses trous — ta valeur serait de dire **comment** les
combler, pas seulement **qu'**ils existent. Extrait direct de la « carte des instruments » (v4.0) :

| Ce qui peut casser | Instrument | État déclaré par l'équipe |
|---|---|---|
| Bug de **compilateur** | tester le compilateur **une fois** (pas chaque app) | ⚠️ script existe, **rien ne le lance** |
| **L'architecte déclare faux** | comparer la **déclaration** au brief (sémantique) | ❌ **inexistant** |
| **Une case manque** | ??? | 🔴 **rien ne le voit — fait à la main** |
| L'executor LLM code mal | le reviewer | ✅ existe (surdimensionné) |
| **Est-ce que ça marche pour un humain ?** | **la Scène (URL live)** | ⏳ récemment construite |

---

## Ce qu'on te demande maintenant

Avec ces faits — **artefact et juges PRÉSENTS pendant les échecs**, **le juge du sens est un LLM
qui ment**, **la convergence agentique a échoué avec juge présent**, **l'usine est hybride depuis
toujours**, **elle savait déjà qu'il fallait sortir l'URL** — **révise ton verdict** :

1. Ton « chemin structurel » (invariants côté vérificateurs + agents sous contrainte) **tient-il
   encore** face au problème du **juge sémantique non fiable** et de la **non-convergence** ? Si
   oui, **par quel mécanisme concret** obtient-on un juge du sens fiable et une convergence garantie ?
2. La distinction **régénération ≠ déterminisme** étant admise : peut-on garder la **régénération**
   (corrige 1× → parc) **sans** perdre la **reproductibilité** — et si oui, comment ?
3. Le vrai goulot n'étant ni l'intelligence ni les juges mais **l'ensemble des cases** (loi du
   contenant) : y a-t-il une façon de **dériver les cases nécessaires à l'avance** (depuis une
   théorie des types d'apps) plutôt que de les découvrir par l'échec humain — **c'était le mandat
   initial**, et il reste le plus important.

*On préfère toujours une remise en question lucide à une confirmation. Mais confronte-la
maintenant aux faits datés, pas au résumé.*
