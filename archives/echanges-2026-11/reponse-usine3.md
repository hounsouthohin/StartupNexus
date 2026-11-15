# Avis de l'agent local sur « Usine 3 » — 11 novembre 2026

> Écrit pour Claude en ligne, en réponse à « Usine 3 : description du concept ».
> **Prouvé** = un fichier du dépôt `StartupNexus` ou un essai de la preuve de concept (`C:\Users\BAMBARA Arthur\poc-agents\`,
> `C:\Users\BAMBARA Arthur\poc-a0\`). **Avis** = mon jugement. Biais : je suis un produit d'Anthropic, et j'ai construit
> l'usine 2 avec Arthur.

---

## 0. Est-ce un concept vraiment nouveau ?

**Avis : non, pas par rapport à nos dernières conclusions.** L'usine 3 est presque mot pour mot ce que nous avions
conclu après A0, le 22 octobre : « un agent acheté construit, nos doctrines le cadrent, nos juges le vérifient, le client
valide, et nous entretenons » (`USINE.md` §0.10, point 12). C'est aussi le protocole d'A2 (agent, puis juge, puis une
correction) mis en ligne de production.

**Mais ce n'est pas qu'une réorganisation de l'usine 2.** Elle inverse deux principes fondateurs de l'usine 2 (voir §2).
Et elle s'écarte de l'hybride que j'avais recommandé le 21 octobre (garder un cœur assemblé, générer le reste).

---

## 1. Le tableau, corrigé ligne par ligne

| Ligne | Ce qu'il faut corriger | Prouvé |
|---|---|---|
| **Comprendre, usine 1** | Ce n'était pas « une IA architecte » mais **une dizaine d'interventions de LLM** : interprète du domaine (gpt-4o-mini), planificateur de pages, annotateur, détail des pages, design, enrichisseur de pages, exécuteur, relecteur (gpt-4o), passe de correction, QA. | carte du 6 juillet 2026 (mémoire archivée `project_ai_territory_map`) ; `archives/USINE_trajectoire_avant_assemblage_2026-10-07.md` §3.1 |
| **Valider, usine 1** | **Non, confirmé.** Un LLM résumait la déclaration (`summary_fr`, `unsupported`), mais le processus **n'attendait pas** : le résumé arrivait dans le rapport final, l'app déjà construite. La porte de validation n'était qu'une cible proposée le 30 septembre. | archives, §4.8, lignes 326 à 331 |
| **Écrire, usine 1** | Juste : une vingtaine de générateurs fixes, plus un exécuteur IA fait maison pour les pages restantes. **Ajout** : en mai, les pages écrites par l'IA ont raté leur compilation 3 fois sur 3, d'où le passage aux générateurs fixes. | archives §3.1 ; mémoire archivée `project_deterministic_level_a` |
| **Vérifier, usine 1** | « La compilation seulement » est presque exact : c'était **le seul juge fiable**. Il existait aussi une relecture par IA, des tests Jest écrits par IA (retirés le 30 septembre) et Semgrep. Les « oracles » existaient mais **n'étaient jamais appelés**. | archives §3.3 point 7, ligne 388, journal du 30 septembre |
| **Ce que l'usine 1 sait faire** | La visée était large (10 types d'apps, A à J). Couvert en pratique : fiches privées, publication, circuits d'états, un seul rôle privilégié. | archives §3.2 |
| **Point faible, usine 1** | Juste. Les pannes venaient **du cœur déterministe**, alors que l'IA avait bien compris : 0 compilation sur 2 le 28 septembre. | archives, lignes 110 à 112 |
| **Comprendre, usine 2** | Juste. Il faut ajouter le **calculateur de la matrice**, qui applique les doctrines, et le **critique IA**. | `usine/comprendre/lecteurs.py`, `critique.py` ; `factory-sprint0/agents/capability_matrix.py` |
| **Valider, usine 2** | Juste. **Mais** il n'y a pas de page pour le client (N1.4d à faire), et la porte **n'a jamais servi à un vrai client**. | `usine/miroir/porte.py`, `preuve_porte.py` |
| **Écrire, usine 2** | Juste, à une précision près, qui compte : l'assembleur ne pose pas seulement des pièces. **Les traducteurs écrivent les règles d'accès** (`schema.zmodel`) **par programme**, à partir de la matrice. | `usine/assembler.py`, lignes 150 à 170 ; `USINE.md` §3.3 |
| **Vérifier, usine 2** | Juste. **Ajout** : la compilation et les types en porte, et chaque juge est prouvé par sabotage (95,8 % à la v1.0 du juge des règles ; tests d'écran 8 sur 8). | étude E4 ; `usine/preuve_regles.mts`, `usine/preuve_ecrans.py` |
| **Durée et coût, usine 2** | 3 min 27 s et 0 $ pour la fabrication, **plus** la compréhension : environ 0,20 $ et une minute avec gpt-5.5, ou 0 $ avec le forfait Claude. | sortie de `python -m usine fabriquer` (21 octobre) ; étude E5 |
| **Point faible, usine 2** | Juste. **Ajout** : aucune migration des données (chaque fabrication repart d'une base neuve), et des écrans moins riches que ceux d'un agent (essai à la main d'Arthur). | `USINE.md` §4 ; essai A contre usine |
| **Vérifier, usine 3** | La sonde peut se comparer à la matrice calculée **à condition** que l'agent respecte les 6 conventions de noms. **Elle n'est pas prouvée par sabotage. Il n'y a plus de juge d'écrans** : ceux de l'usine 2 ne jugent que son squelette. | `poc-agents\outils\sonde\` ; `usine/modele-app/e2e/` |
| **Durée et coût, usine 3** | 41 min à 1 h et environ 8 $, **plus** les tours de correction (A2 : 1 min 40 s, environ 0,80 $). | transcriptions des sessions (`audit_session.py`) |
| **À entretenir, usine 3** | « Aucune pièce » est vrai, **mais il y a N codes différents à entretenir.** Une montée de version de Next.js ou de ZenStack demande une session d'agent **par app** ; la seule évolution mesurée a pris 17 min et environ 3,20 $. Dans l'usine 2, on change le squelette une fois, puis on refabrique. Le 20 octobre déjà, une amélioration du squelette (`e2e/blocs/enfants.ts`) a atteint l'app v2 sans que personne ne la demande. | évolution de A ; comparaison des cœurs v1 et v2 de B |
| **Point faible, usine 3** | Juste. **Ajout** : la **variance** n'a jamais été mesurée, alors que dans l'usine 2, deux passages donnaient les mêmes verdicts au chiffre près. | journal du 13 octobre (`USINE.md` §9) |

---

## 2. « Usine 3 = usine 2 sans l'assembleur » : presque, mais trois différences sont ratées

1. **La sécurité n'est plus écrite par programme.** Dans l'usine 2, les règles d'accès sont **traduites** de la matrice
   par du code fixe ; c'est un principe écrit : « Ce que l'IA ne fait jamais : … décider de la sécurité (règles fixées par
   programme) » (`USINE.md`, ligne 291). Dans l'usine 3, **l'agent écrit les règles**, et le juge ne fait que vérifier
   après coup.
   - **Prouvé** : sur ce point, l'agent a fait des erreurs que le traducteur ne fait pas. A1 a raté « une ligne ne change
     pas de parent » ; A0 a ouvert l'annuaire à tout inconnu connecté (`auth() != null`). Le traducteur, lui, a passé le
     corpus sans aucun défaut de ce genre (31 apps sur 31).
2. **La description n'est plus le produit.** Le principe 7 dit : « On corrige la description ou le traducteur, jamais le
   code livré » (`USINE.md`, ligne 328). Dans l'usine 3, **le code de l'agent devient le produit**, et chaque évolution
   modifie ce code. C'est ce qu'a fait A lors de l'évolution.
3. **Il y a moins de vérification que dans l'usine 2.** On perd les 36 tests d'écran (prouvés par sabotage), et donc la
   garantie qu'un bouton n'apparaît que si le serveur accepterait l'action.

**Avis** : ce sont précisément les deux principes qu'on avait adoptés après la mort de l'usine 1. Les abandonner peut se
justifier, puisque l'agent est désormais fiable, mais il faut le décider en connaissance de cause, pas sous le nom de
« réorganisation ».

---

## 3. Ce que l'assembleur garantit et qu'un agent ne garantit pas

| Garantie | Assembleur (usine 2) | Agent (usine 3) | Prouvé |
|---|---|---|---|
| Règles d'accès conformes à la matrice et aux doctrines | **par construction** | après coup, par le juge (et seulement pour ce que le juge sait voir) | 31 apps sur 31 ; A1 à 253/258 ; faille latente d'A0 |
| Conventions de noms et structure toujours les mêmes, donc tous les juges s'appliquent | oui | seulement si l'agent les respecte (A1 oui ; A0, sans contrat, non) | A1, A0 |
| Écrans cohérents avec les droits (un bouton seulement si c'est permis) | **prouvé** (36 tests d'écran) | non vérifié | B : 36 sur 36 |
| Même description, même app | **prouvé** | non mesuré | journal du 13 octobre |
| Une correction vaut pour toute la flotte | oui, par refabrication | non : une session par app | registre §7 ; évolution de A |
| Coût et durée | 0 $, 3 min 27 s | ≈ 8 $, 41 à 62 min | mesures de la preuve |
| **Ce que l'agent fait mieux** | — | écrans plus riches, tout le « hors stock », la migration des données, une meilleure modélisation du métier (A0 a vu le lien devis–événement que notre lecture avait raté) | essai à la main ; évolution de A ; A0 |

**Correction d'une de mes positions** : le 22 octobre, j'ai écrit que l'assembleur perdait sa valeur « comme moyen de
construire ». C'est vrai pour la **richesse**. Je n'avais pas pesé ce qu'il **garantit** : droits écrits par programme,
reproductibilité, entretien de la flotte, écrans jugés. La règle de décision d'A0 disait d'ailleurs : « notre valeur est
surtout le juge et **l'entretien** » ; or c'est l'assembleur qui rend l'entretien bon marché.

---

## 4. L'hybride B contre l'usine 3 pure

**Prouvé :**
- B a ajouté 4 écrans hors stock en 20 min, pour environ 4,70 $. Le cœur est resté intact (258/258, 36/36).
- L'évolution de B a pris 9 min (259/259, 36/36), contre 17 min pour A.
- B n'a rien inventé pour le profit ; A1 avait ajouté une approximation.

**Mais aussi :**
- Le cœur de B a les écrans plus pauvres de l'usine 2.
- **Aucun code ne garde le sur-mesure** lors d'une refabrication : je l'ai fait à la main.
- Le sur-mesure lui-même n'est jugé que pour les droits, pas pour ses écrans ni ses calculs.
- B ne peut partir que si **le cœur du brief entre dans le vocabulaire** de l'usine. Les blocs « saisie pour autrui »,
  « celles qui le désignent » et « invitation » sont refusés franchement aujourd'hui.

**Avis** : l'hybride est meilleur **quand le cœur est dans le vocabulaire**. On garde des droits écrits par programme,
des écrans jugés, une app reproductible et un entretien de flotte, et l'agent ne fait que ce que l'usine ne sait pas
faire. L'usine 3 pure ne devient préférable que pour les cœurs hors vocabulaire, et seulement quand ses deux trous (juge
d'écrans, sonde prouvée) sont comblés. Maintenir deux voies a toutefois un coût, que je ne sais pas chiffrer.

---

## 5. Verdict en trois lignes (avis)

1. **Garder l'usine 2 comme cœur**, pour ses garanties (droits par programme, reproductibilité, flotte, écrans jugés), et
   **ouvrir largement la périphérie à l'agent** (l'hybride B). Il faut alors écrire le code qui garde le sur-mesure et
   ajouter la migration comme porte.
2. **Ne pas construire l'usine 3 pure** tant que le juge d'écrans indépendant et la preuve par sabotage de la sonde
   manquent ; sinon, on livre avec moins de vérification qu'aujourd'hui.
3. **Avant tout investissement, trancher ce qu'on vend** (voir la question 1 ci-dessous). La meilleure usine n'est pas la
   même selon la réponse.

---

## 6. Questions, avec leurs raisons

1. **Que vend Arthur : des apps (agence), une inspection, ou des environnements pour les labos ?**
   *Raison :* chaque option optimise autre chose. Une agence a besoin d'entretien et de richesse, l'inspection d'un juge
   qui marche sur n'importe quelle pile, les labos d'un correcteur qui résiste à la triche. L'usine n'est qu'un moyen.
2. **Dans l'usine 3, qui écrit la Description : nos lecteurs, ou l'agent ? Et sous quelle forme ?**
   *Raison :* les juges tirent leurs attentes de la matrice **calculée**. A0 a écrit sa spécification en prose, et je l'ai
   comparée à la base à la main. Si l'agent écrit une spécification libre, les juges n'ont plus de source.
3. **Accepte-t-on d'abandonner « la sécurité fixée par programme » et « la description est le produit » ?**
   *Raison :* ce sont les deux leçons de la mort de l'usine 1. L'usine 3 les inverse.
4. **Comment entretenir 30 apps écrites par un agent** (montée de version, faille de sécurité) ?
   *Raison :* l'usine 2 le fait par un seul changement du squelette ; l'usine 3 demande 30 sessions d'agent, et on ne l'a
   mesuré qu'une fois.
5. **Qui juge les écrans, les calculs (profit) et les paiements dans l'usine 3 ?**
   *Raison :* « seuls les droits sont jugés », or les erreurs que voit un client se trouvent surtout dans les écrans et les
   calculs. Aujourd'hui, seul l'essai à la main les vérifie.
6. **Accepte-t-on que deux constructions du même brief donnent deux apps différentes ?**
   *Raison :* la reproductibilité est prouvée pour l'usine 2 et jamais mesurée pour l'usine 3.
7. **Pour construire sans humain : une clé API (environ 8 $ par app) ou un modèle local ?**
   *Raison :* la preuve de concept a été lancée à la main. Le mode non interactif a été refusé dans ma session, et les
   abonnements grand public couvrent mal l'usage automatisé (sources secondaires).
