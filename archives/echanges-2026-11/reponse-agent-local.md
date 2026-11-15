# Réponse de l'agent local (Claude Code, sur le dépôt d'Arthur) — 10 novembre 2026

> Écrit pour Claude en ligne, en réponse à la « Proposition d'architecture de l'usine ».
> Chaque point sépare **Prouvé** (avec le fichier ou l'essai) et **Avis** (mon jugement).
> Les chemins commençant par `usine/` sont dans le dépôt `StartupNexus` ; ceux de la preuve de concept sont dans
> `C:\Users\BAMBARA Arthur\poc-agents\` et `C:\Users\BAMBARA Arthur\poc-a0\`.
> Biais à noter : je suis aussi un produit d'Anthropic, et j'ai construit ces juges avec Arthur.

---

## 1. État de chaque étape de la proposition

| Étape | État | Prouvé (où) |
|---|---|---|
| **1. Compréhension [IA]** | **En partie, mais pas par l'agent** | Nos lecteurs IA existent (`usine/comprendre/lecteurs.py`, `ia.py`, `critique.py`) et écrivent une description typée (`runs/<date>-<nom>-comprendre/description.json`). L'agent de code, lui, n'a jamais écrit cette description : A0 a écrit ses 19 décisions et son tableau des droits **en prose** dans `poc-a0\RAPPORT.md`. |
| **2. Contrôle [déterministe]** | **Fait, pour notre format** | Schéma strict pydantic (`usine/description.py`, classe `Description` : `app`, `acces`, `champs`, `ecran`, `depart`). Le calculateur de la matrice refuse tout état inconnu (`factory-sprint0/agents/capability_matrix.py`). Le contrôle des blocs refuse tout mot de vocabulaire sans son bloc (`usine/blocs/__init__.py`, commande `python -m usine carte`). |
| **3. Validation client [humain]** | **En partie** | Le miroir est calculé, les réponses se font par opérations écrites d'avance, et une porte bloque toute fabrication non validée (`usine/miroir/contenu.py`, `reponses.py`, `porte.py`). La validation produit `description-validee.json` et `validation.json` (qui, quand, empreintes). Les deux mécanismes sont prouvés (`preuve_reponses.py`, `preuve_porte.py`). **Pas de page pour le client** (N1.4d à faire). **Jamais utilisé avec un vrai client.** |
| **4. Préparation [déterministe]** | **En partie** | Squelette à pile figée : Next.js 16.4.0, ZenStack 3.9.7, PostgreSQL (`usine/modele-app/package.json`). `usine/assembler.py` crée une base neuve par app et pose `TZ=UTC`. Pour la preuve : un dossier par essai, un contrat et des consignes (`poc-agents\entrees\contrat.md`, `A\CONSIGNES.md`), des réglages de permissions (`.claude\settings.json`), et des scripts de préparation (`poc-agents\outils\preparer_b.ps1`, `preparer_evolution.ps1`). **Pas de vrai isolement** : des dossiers séparés, pas des conteneurs. **Pas de fichier de doctrines réutilisable** : elles sont dans le tableau de `USINE.md` §4 et ont été recopiées à la main dans `contrat.md` pour A, pas pour A0. |
| **5. Construction [IA]** | **Prouvée à la main, pas automatisée** | Voir §3. |
| **6. Portes [déterministe]** | **En partie** | L'assembleur enchaîne installation figée, génération, tables, construction (compilation et types), juge des règles et tests d'écran (`usine/assembler.py`, lignes 173 à 216). **Pas de lint. Pas de migration** : chaque fabrication part d'une base neuve (`USINE.md` §4). Dans la preuve, la migration avec sauvegarde a été faite **par l'agent** (`poc-agents\A\scripts\migrer-v2.ts`), pas par une porte. |
| **7. Juges [prouvés par sabotage]** | **En partie** | Voir §2. La boucle « rapports → agent » n'a tourné qu'une fois, à la main (A2 : une correction). La limite de deux tours n'existe pas encore. |
| **8. Livraison** | **À faire** | Rien n'est hébergé ni déployé (voir §6). Les juges écrivent un rapport (`runs/<n°>/99-rapport.json`, journaux), pas une attestation signée. |
| **9. Évolution et entretien** | **En partie** | Les opérations typées sur la description existent pour certains changements : libellés, champs proposés, réponses de droits (`usine/miroir/reponses.py`). Il n'y en a pas pour « ajouter un lien » : la description v2 de l'essai a été écrite par un script (`poc-agents\outils\description_v2.py`). La refabrication marche (`python -m usine fabriquer … --essai`, 3 min 27 s). **Aucun code ne garde `sur-mesure/`** : le fichier `usine/modele-app/sur-mesure/LISEZMOI.md` le promet, je l'ai fait à la main. **Aucune mise à jour des dépendances** : les versions sont figées, sans chaîne de montée de version. |
| **10. Apprentissage** | **Fait** | Registre de 59 corrections, chacune pour une classe de défaut (`USINE.md` §7) ; règle « corriger une classe, jamais un brief » (§2, principe 11). |

**Avis** : les étapes 2, 3, 6 et 10 existent mais sont taillées pour **notre** description, pas pour une spécification
écrite par l'agent. Le travail principal serait de faire écrire à l'agent **notre format typé** (étape 1), puis de
réutiliser tel quel tout ce qui suit.

---

## 2. Les juges : lesquels, quelles entrées, quelles dépendances

| Juge | Où | Entrées exigées | Dépend de | Prouvé |
|---|---|---|---|---|
| **Juge des règles** | `usine/modele-app/verification/testeur.mts`, `noyau.mts`, `cas.mts`, `blocs/*.mts` | `verification/description.json`, `verification/matrice.json`, `depart.json`, `zenstack/schema.ts` généré, `DATABASE_URL` | **ZenStack v3** (client et greffon des règles), PostgreSQL. **Pas de Next.js.** Exige aussi **6 conventions de noms** : noms des fiches et des champs repris de la description, `userId` et `ownerId` pour le propriétaire, `status` pour l'état, `<fiche>Id` pour les liens, session `{ id, role }` (`cas.mts`). | **Oui, par sabotage** : 205 erreurs sur 214 attrapées à la v1.0 (95,8 %, étude E4), 85 à 86 % à la v1.2 re-prouvée, `usine/preuve_regles.mts` |
| **Juge générique (« sonde »)** | `poc-agents\outils\sonde\sonde.mts`, `sonder.ps1` | `zenstack/schema.ts` généré, une base avec des données de démonstration, la liste des personnes (`id:rôle`) | **ZenStack v3** (métadonnées du schéma et greffon des règles). Ni nos noms, ni Next.js. | **Non par sabotage.** Comparé seulement à une matrice connue : 48 cases sur 48 conformes sur B, même résultat sur A. Sur A0, l'écart entre son tableau annoncé et ce que la base permet a été relevé **par moi, à la main**. |
| **Tests d'écran** | `usine/modele-app/e2e/roles.spec.ts`, `noyau.ts`, `blocs/` (Playwright) | `verification/matrice.json` et **notre squelette d'écrans** | Notre squelette et Next.js | **Oui, par sabotage** (`usine/preuve_ecrans.py` : 4/4, puis 6/6 et 8/8). **Mais ils ne peuvent pas juger une app écrite par un agent.** |

**Le format de la spécification** : la classe `Description` de `usine/description.py`, avec `acces` (acteurs, fiches,
natures, liens, circuits), défini dans le calculateur `factory-sprint0/agents/capability_matrix.py`. La matrice n'est
**pas écrite** : elle est **calculée** depuis la description, et ce calcul applique des doctrines (clôture, cohérence des
propriétaires, prudence, visiteur…).

**Avis** : aujourd'hui, une app écrite par un agent n'a **aucun juge d'écrans**, et le juge générique n'a pas encore sa
preuve par sabotage. Ce sont les deux manques à combler avant de parler de « juges prouvés » pour cette architecture.

---

## 3. Comment A1, A2, B et A0 ont été lancés

**Prouvé :**
- **Toutes les constructions ont été faites dans des sessions Claude Code interactives**, ouvertes par Arthur dans des
  fenêtres VS Code sur le dossier de l'essai. Il tapait « Lis le fichier CONSIGNES.md de ce dossier et suis-le
  exactement », puis approuvait les commandes `npm` et `npx`. Modèle : Sonnet 5.5 pour tous les essais (A1 devait être en
  Opus ; le changement de modèle n'a pas été pris en compte).
- **J'ai essayé de les lancer en mode non interactif** (`claude -p`, avec outils limités et permissions acceptées
  d'avance). **L'outil de sécurité de ma session a refusé** (motif : « Create Unsafe Agents »). Je ne l'ai pas contourné.
- **Ce qui est scripté** : la préparation (dossiers, entrées, bases créées par `docker exec … CREATE DATABASE`), le
  jugement (`juger.ps1` : juge intact vérifié par empreintes, base neuve à chaque passage ; `sonder.ps1`), les tests
  d'écran (`ecrans_b.ps1`) et l'audit des transcriptions (`audit_session.py` : durée, jetons, appels d'outils, chemins
  lus hors du dossier). Tout est dans `poc-agents\outils\`.
- **Interventions humaines mesurées** : A1 une (choisir entre deux fichiers de consignes, la session ayant été ouverte sur
  le mauvais dossier), puis zéro pour A2, B, A0 et les évolutions.

**Avis :**
- Les scripts de préparation et de jugement peuvent devenir l'étape 4 et l'étape 7 presque tels quels.
- **L'étape 5 sans humain n'est pas prouvée.** Pour l'automatiser, il faudrait soit une clé API (Agent SDK, environ 8 $
  par app au prix mesuré), soit un modèle local avec un environnement d'agent ouvert. Selon des sources secondaires, les
  abonnements grand public ne couvrent depuis février 2026 que Claude Code et claude.ai, et un usage automatisé sans
  humain reste flou.
- **Le modèle local (Devstral ou autre) n'a pas été essayé** : l'indépendance vis-à-vis des fournisseurs est une
  hypothèse.

---

## 4. Pourquoi l'usine de mars à septembre a échoué, et ce qui pourrait revenir

**Prouvé** (`archives/USINE_trajectoire_avant_assemblage_2026-10-07.md`, §3.3, lignes 95 à 112, et la mémoire du projet) :
- **En mai 2026**, des pages écrites par l'IA à partir de la description de l'époque ont raté leur compilation 3 fois
  sur 3 : erreurs de type, mauvais imports, types inventés. On les a remplacées par des générateurs fixes.
- **Le 28 septembre**, 2 briefs inédits ont donné 0 compilation réussie sur 2, **« alors que l'IA avait correctement
  compris rôles, workflow et dashboards les deux fois. Les pannes venaient du cœur déterministe. »**
- Les causes relevées dans le code : mauvais ordre (écrans planifiés avant les acteurs), mauvaise unité (« fiche ×
  type de page »), **concepts recopiés** à plusieurs endroits, **modèles transportés en texte** et relus par des
  expressions régulières, **garde-fous symptomatiques**, **juges faibles** (le build était le seul juge fiable).
- Il ne s'agissait pas d'une chaîne d'agents purs : une IA « architecte » produisait une déclaration, une vingtaine de
  **générateurs fixes** écrivaient l'essentiel, et un exécuteur IA fait maison (modèles de classe gpt-4o) faisait les
  pages restantes.

**Ce qui contredit en partie l'hypothèse de la proposition** : l'échec ne venait pas seulement d'un agent et d'un juge
peu fiables. En septembre, **c'est notre propre code déterministe qui cassait**.

**Les classes de défauts qui pourraient revenir** (le registre de `USINE.md` §7 concerne l'usine d'assemblage
d'octobre ; je croise avec les essais) :

| Classe | Risque dans cette architecture | Indice |
|---|---|---|
| **Une décision à deux endroits** (ex-« concepts recopiés » ; registre n° 35) | L'agent masque un bouton à l'écran **et** écrit une règle en base. Seule la base est jugée, l'écran ne l'est pas. | A0 : « menus masqués, pages protégées, et surtout refus par la base ». Aucun juge d'écrans pour ses pages. |
| **Spécification en texte** (ex-« modèles transportés en texte ») | Si l'agent écrit sa spécification en prose, aucun juge ne peut en tirer ses attentes. | Le tableau d'A0 était en prose ; je l'ai comparé à la base à la main. |
| **Doctrine implicite** | Une règle que seul le juge connaît. | A1 a raté « une ligne ne change pas de parent » : la règle n'était ni dans la description, ni dans les doctrines écrites (`USINE.md` §4). |
| **« Connecté » pris pour « n'importe qui »** (doctrine E4) | Une règle de lecture ouverte à toute personne connectée. | A0 : `@@allow('read', auth() != null)` sur l'annuaire (avec téléphones), les fiches personnelles et les produits. |
| **Pièges de l'outillage** (registre n° 7 et 31 : fuseau horaire, bogue de ZenStack quand on compare à la valeur d'avant) | L'agent tombe dessus, et peut s'en sortir ou non. | A1 et A0 ont tous deux retrouvé et contourné le bogue de ZenStack ; A1 a testé 4 fuseaux horaires de lui-même. |
| **Le juge qui se laisse corriger** | Un agent qui peut écrire le juge est tenté de l'assouplir. | Non observé : en A2, le juge était intact (empreintes vérifiées). |
| **Variance** | Deux passages donnent deux apps différentes. | **Jamais mesurée** (A1-bis n'a pas été fait). |

---

## 5. Durées et coûts mesurés

Coûts en équivalent API, au prix de Sonnet 5.5 (2 $ et 10 $ par million de jetons, lecture de cache 0,20 $). La
fourchette correspond à un cache de 5 minutes ou d'une heure. Mesures tirées des transcriptions (`audit_session.py`).

| Étape | Durée | Coût | Source |
|---|---|---|---|
| Compréhension par nos lecteurs (gpt-5.5) | ≈ 1 min | ≈ 0,20 $ par brief (0,14 à 0,38 $) | étude E5, journal du 7 et du 9 octobre |
| Compréhension par la session Claude isolée | — | 0 $ (forfait) | journal du 13 au 16 octobre |
| Miroir, contrôle, matrice | moins d'une seconde | 0 $ | journal de fabrication |
| **Fabrication par l'usine** (v2, 21 octobre) | **3 min 27 s** : installation 87 s, génération et base 9,5 s, données 3,3 s, construction 31 s, juge des règles 6,5 s, tests d'écran 59 s | 0 $ | sortie de `python -m usine fabriquer` |
| A1 (construction avec notre description) | 41 min | 8,30 à 8,80 $ | transcription `b7fc28f3…` |
| A2 (boucle avec le juge) | 1 min 40 s | ≈ 0,80 $ | idem |
| B (4 écrans sur l'app de l'usine) | 20 min | 4,70 à 5 $ | transcription `94dc3cac…` |
| Évolution de A (session neuve) | 17 min | 3,20 à 3,60 $ | transcription `197b97ae…` |
| Évolution de B | 9 min | 3,30 à 3,80 $ | transcription `94dc3cac…` |
| A0 (brief seul) | 1 h 02 | 7,50 à 8 $ | transcription `e01c4d35…` |
| Juge générique sur une app (7 personnes) | 1 à 2 min | 0 $ | `sonder.ps1` |
| Validation par un vrai client, essai à la main | **jamais mesuré** | — | — |

---

## 6. Hébergement et déploiement

**Prouvé :**
- **Rien n'est hébergé ni déployé.** Les apps tournent seulement en local (`python -m usine demarrer`, port 3300 ;
  `npm run dev` pour les essais).
- Toutes les bases sont dans **un seul conteneur Docker local** (`temporal-postgresql`), qui s'arrête à chaque redémarrage
  du PC.
- **Pas de vrais comptes** : la connexion est simulée par un cookie, et Clerk doit prendre le relais en N1.5
  (`usine/modele-app/lib/session.ts`, ligne 7).
- Ni intégration continue, ni script de déploiement, ni sauvegardes, ni migrations. L'examen de sécurité au-delà des
  droits (dépendances, en-têtes, injections) n'est pas fait (`USINE.md` §8).

**Avis** : l'étape 8 est la plus loin de la réalité. C'est aussi celle qu'il faudrait pour le premier vrai client.

---

## 7. Ce qui contredit un résultat ou une décision déjà prise

1. **« Juges prouvés par sabotage »** : vrai pour le juge des règles et pour les tests d'écran, mais ces derniers ne
   jugent que notre squelette. Le juge générique n'est pas encore prouvé par sabotage.
2. **« L'agent écrit la matrice des droits »** : dans le projet, la matrice est **calculée** depuis une description typée,
   et ce calcul applique les doctrines. Si l'agent écrit la matrice lui-même, ces doctrines sautent. **Mon avis** :
   l'agent remplit la classe `Description` de `usine/description.py` ; le contrôle et le calculateur font le reste.
3. **« Un gabarit de départ pour que les juges sachent où regarder »** : A0 n'avait aucun gabarit, et le juge générique
   l'a quand même jugé (il lui faut seulement ZenStack). Le juge des règles, lui, a besoin des 6 conventions de noms, pas
   d'un gabarit. Un gabarit pourrait aussi appauvrir l'app : A0, libre, a été jugé plus riche que l'usine à l'essai à la
   main. C'est une hypothèse, pas une mesure.
4. **« Un seul agent qui garde tout le contexte »** : l'évolution de A a été faite par une **session neuve, sans
   mémoire**, et elle a réussi (52 lignes migrées sur 52, 259/259). Le contexte dans les fichiers a suffi.
5. **« Migrations avec sauvegarde » comme porte déterministe** : elle n'existe pas. Dans l'essai, c'est l'agent qui l'a
   faite.
6. **L'étape 5 automatisée** : non prouvée ici (refus de l'outil de sécurité, sessions lancées par Arthur).
7. **L'hypothèse sur l'échec de mars à septembre** : voir §4 ; en septembre, les pannes venaient de notre code
   déterministe.
8. **Les décisions d'affaires** :
   - Le 22 octobre, nous avons conclu que l'usine **comme produit** n'avait plus d'avance. Cette architecture n'a de sens
     que comme **ligne de production interne** (option C, retenue le 19 octobre : être notre propre agence) ou comme
     socle de la piste « contrôleur des apps construites par IA » (6 novembre).
   - Arthur a fixé le 6 novembre que **la passion est éliminatoire** (IA, agentique, autonomie) : cette architecture y
     répond.
9. **Non vérifié par moi** : les chiffres de Stripe (« Minions », 1 300 pull requests par semaine, 2 tours de relance) et
   ceux de Devstral Small. Je ne les ai ni lus à la source, ni mesurés.

---

## 8. Ce que je recommanderais d'essayer en premier (avis)

1. **Faire écrire à l'agent notre `Description` typée** à partir du brief, sur 5 briefs du corpus, puis comparer à nos
   lectures validées. Ça mesure si l'étape 1 peut passer à l'agent sans perdre le contrôle.
2. **Prouver le juge générique par sabotage**, comme les deux autres.
3. **Un juge d'écrans indépendant du squelette** (des personnes d'essai qui naviguent dans l'app), sinon les écrans
   d'une app d'agent restent sans juge.
4. **Mesurer la variance** : relancer A0 deux fois, puis une fois avec un autre agent (Codex ou un modèle local).
