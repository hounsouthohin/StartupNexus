# USINE — le plan de match (depuis le 13 novembre 2026)

> **Fait foi.** Ce document ne garde que ce dont on a besoin pour construire. Tout le reste est archivé, intact :
> - l'ancien USINE.md (réflexion d'octobre-novembre au §0.10, chaîne détaillée au §3, registre n° 1 à 59 au §7,
>   journal au §9) : [`archives/USINE_avant_plan_2026-11-13.md`](archives/USINE_avant_plan_2026-11-13.md) ;
> - les échanges de novembre avec Claude en ligne : [`archives/echanges-2026-11/`](archives/echanges-2026-11/).
>
> **Le détail technique de chaque mécanisme** (agent, boîte, juges, sabotages, assembleur, orchestrateur…) est dans
> [`conception-technique.md`](conception-technique.md). Ici : le but, les règles, l'existant, le plan, les inconnues.

---

## 1. Le but et le concept

**Le but.** Arthur construit **sa propre usine à apps web**. Elle automatise complètement le développement d'une app :
comprendre la demande, la faire valider, construire, prouver, livrer, faire évoluer. Limitée au départ, elle
**s'agrandit** capacité par capacité. Le côté commercial viendra plus tard ; les premiers clients seront accueillis en
personne.

**Le concept, validé le 13 novembre : une usine hybride, avec l'inspecteur au centre.**

```
demande ──► LIRE ──────────► MIROIR ──────────► ASSEMBLER ─────────► AGENT ───────────► JUGES ──────────► livrer
            (IA : 7 lecteurs, (le client valide ; (programme : données, (IA enfermée dans   (programmes indépendants,
             Description       rien ne se         droits calculés,      une boîte : écrans  prouvés par sabotage ;
             typée)            construit avant)   doctrines → le cœur)  riches, périphérie) 2 corrections au plus,
                                                                                            puis un humain)
```

En image : **une maison**. Le plan est signé par le client (le miroir). La structure est préfabriquée en usine (le cœur
assemblé). Un artisan fait les finitions (l'agent). Un inspecteur qui ne dépend pas de l'artisan vérifie tout
(les juges). Le catalogue dit ce qu'on sait construire (les capacités).

**L'usine grandit par capacités admises.** Une capacité (tableaux de bord, calendrier, fichiers joints, calculs,
recherche, notifications…) n'est admise que si son dossier est complet :
- le vocabulaire de la Description ;
- le contrat ;
- les pièces fixes, seulement là où il y a des droits ou de l'argent ;
- la documentation pour l'agent ;
- la doublure locale pour les essais ;
- les juges, les sabotages et la preuve.

Son état (refusée, en essai, admise) est **calculé par programme**, comme la carte des blocs aujourd'hui. Une seule
recette sert pour toutes : aucune capacité n'est un cas à part (détail : `conception-technique.md` §8 et §16.9).

**Les six niveaux** (validés le 11 nov) : 1 gestion simple (en grande partie fait en octobre) · 2 gestion enrichie
(calculs, tableaux de bord, calendrier, fichiers, notifications) · 3 apps connectées · 4 temps réel · 5 apps
intelligentes · 6 plateformes.

---

## 2. Les règles qui ne bougent pas

### 2.1 Les trois zones (qui écrit quoi)

| Zone | Contenu | Qui l'écrit |
|---|---|---|
| **Cœur** | données, droits, porte, juges, argent | écrit une fois, relu, prouvé ; posé par l'assembleur depuis la matrice calculée ; **jamais généré par une IA pour une app** |
| **Déclarations** | formules, indicateurs, règles métier, raccordements | décrites dans la Description, contrôlées et compilées par l'usine |
| **Bords** | écrans riches, design dans le système de design, documents, intégrations | **l'agent**, dans `sur-mesure/`, contre des contrats typés ; il n'accède aux données que par le client ZenStack de la personne connectée, **ce qui doit l'empêcher** de faire fuir des données. *(Précisé le 19 nov, relevé par Codex : c'est à prouver. Les règles de ZenStack s'appliquent du côté de l'application, et la garde des personnalisations n'est pas encore construite.)* |

Deux conséquences :
- l'agent **ne crée aucune table** et n'écrit aucun droit ; s'il en a besoin, il le **propose** (`signaler`) ;
- une pièce fixe n'existe que là où une erreur fuirait en silence (les droits d'un fichier, un montant qui engage de
  l'argent, un envoi qu'on ne doit pas perdre).

### 2.2 Les principes (acquis en octobre, confirmés par les essais)

1. **Loi du contenant** : une intention sans structure typée pour la porter s'évapore. Étendre l'usine, c'est ajouter du
   vocabulaire, pas enseigner à l'IA.
2. **Une seule source par concept** : la matrice est calculée une fois ; règles, écrans, menus, tests et miroir en
   dérivent.
3. **L'app, ce sont des acteurs qui déroulent un processus sur des fiches** : on conçoit par acteur, pas par écran.
4. **Affordance honnête** : un bouton n'apparaît que si le serveur accepterait l'action.
5. **Clôture contre désir** : l'usine complète ce qui est impliqué par nécessité ; le reste remonte au client par le
   miroir. Dans le doute : désir.
6. **La Description est le produit** : on corrige la Description ou l'usine, jamais le code livré.
7. **Moindre privilège** : un oubli donne un manque visible, jamais une fuite invisible.
8. **Des blocs complets** : un mot de vocabulaire sans son bloc empêche de fabriquer ; un mot pas encore construit est
   refusé franchement.
9. **Corriger une classe, jamais un cas** : aucune correction propre à un brief ; **on n'assouplit jamais un juge** ;
   chaque correction va au registre (§7).
10. **Avant, pendant, après** : accord d'Arthur avant (fiche courte) ; défauts corrigés et inscrits pendant ; après,
    une mesure et un critère d'arrêt fixé d'avance.

### 2.3 Les règles des juges et de l'agent

- **Le constructeur ne voit ni ne touche ses juges.** Ils tournent dans des conteneurs séparés.
- **Un juge tire ses attentes de la source validée** (la Description, la matrice), jamais du fichier qu'il juge.
- **Un juge n'est cru qu'une fois prouvé**, par des sabotages (on casse exprès, il doit le voir) et par des témoins
  (l'app intacte, il doit dire conforme). Un juge qui hésite est mis à l'écart.
- **Une IA n'est jamais l'oracle** de ce qui a été produit. Elle peut donner un avis, jamais un verdict.
- **Un verdict porte ses empreintes** (relecture du 16 nov) : celles du juge, de l'app jugée, de la description, des
  données de départ et du navigateur. Un résultat sans empreinte, ou d'une autre version, ne compte pas.
- **Un juge refuse de juger** une description dont l'empreinte ne concorde pas avec celle que la porte a enregistrée à
  la validation.
- **Les juges sont la constitution de l'usine.** C'est le seul code où une erreur passe en silence. Chaque juge a donc
  sa fiche « ce que je vérifie / ce que je ne vérifie pas », validée par Arthur, et son code est gardé court.
- **Ce sont les juges qui cochent les tâches de l'agent**, pas l'agent lui-même.
- **Les consignes expliquent, la boîte impose.** Aucune sécurité ne repose sur l'obéissance de l'agent.
- **On ne livre que ce qu'on sait vérifier.**

### 2.4 Les données et la visibilité

- **Aucune donnée réelle dans l'usine** : demandes fictives ou sans données personnelles, données de démonstration ;
  les vraies données ne vivent que dans l'app livrée.
- **Développement de l'usine, sur l'abonnement d'Arthur**, mais seulement dans l'« usage ordinaire de Claude Code »
  que prévoient les conditions d'Anthropic (page officielle lue le 14 nov) :
  - Claude Code qui code lui-même : il construit l'usine, et il est l'artisan des essais ;
  - la boîte aux lettres des lecteurs : à petit volume, pour des mesures de développement.
  **Jamais** l'abonnement comme « cerveau » d'un autre agent (mini-swe-agent) : cela attend l'API. **Vrais clients et
  gros lots** : par l'API, sous conditions commerciales.
- **La vue lit, elle ne façonne pas** : l'usine écrit des événements complets dès le premier jour ; une salle de
  contrôle les lira plus tard. La visualisation ne dicte jamais l'architecture (l'erreur de l'usine Temporal).

### 2.5 La circulation de l'information (7 règles, 30 sept)

Un fait = un seul auteur · entre machines, des données, jamais du texte · contrôle strict à chaque frontière (une
réponse invalide est refusée, l'erreur renvoyée) · fiches figées · l'IA reçoit le minimum · les ordres viennent du plan,
pas de l'IA · chaque fichier sait de quelle case il vient.

---

## 3. L'existant (ce qui marche déjà, et où)

### 3.1 Dans le dépôt

| Où | Quoi | Commande |
|---|---|---|
| `usine/comprendre/` | les 7 lecteurs IA, contrôles stricts, plafond de dépense ; modèle `boite` = la session isolée | `python -m usine comprendre <brief> --nom X --modele boite` |
| `usine/miroir/` | le miroir calculé (phrases par rôle, questions, hors stock, refus et variantes), sa couverture prouvée | `python -m usine.miroir runs/<lecture>` |
| `usine/description.py` | la forme stricte de la Description (11 types de champs, refus codés `[bloc:…]`) | — |
| `usine/calculateur/` | **le calculateur de la matrice** et son banc (14 matrices attendues, toutes identiques) | `python -m usine.calculateur.banc --summary` |
| `usine/traduire/`, `usine/modele-app/` | traducteurs (schéma et règles ZenStack, notice, droits d'écran, départ) et squelette fixe, avec ses juges livrés (`verification/`, `e2e/`) | — |
| `usine/assembler.py` | la fabrication en 10 étapes | `python -m usine fabriquer <description> [--essai]` |
| `usine/blocs/` | le catalogue des blocs, le contrôle d'architecture, la carte | `python -m usine carte` |
| `usine/preuve_regles.mts`, `usine/preuve_ecrans.py` | les preuves des juges par sabotage | voir `usine/ESSAIS.md` |
| `usine/preuve_audit.py` | la preuve du contrôle des failles connues (étape 5 de la fabrication) | `python -m usine.preuve_audit` |
| `conception/` | **les dossiers de conception**, un par pièce, relus avant de développer | `conception/LISEZMOI.md` |
| `conception/carte-de-l-usine.html` | **la carte visuelle de l'usine** (schémas), mise à jour à chaque fin de travail | https://claude.ai/artifact/8ynHYQ1riEst6F4FjhJEYh |
| `usine/repetition.py`, `usine/mesures/` | rejouer des lots de briefs ; mesures contre des grilles écrites d'avance | `python -m usine.repetition --chaine-reelle [--corpus usine/corpus]` |
| `usine/briefs_reels/` | 5 premiers vrais briefs ; lot d'**apprentissage** (10, avec sa grille et les sorties de l'étude 05) ; lot d'**examen** (10, **à ne pas ouvrir**) | — |
| `usine/corpus/` | corpus 2 : 33 vrais briefs, règle de choix et périmètre attendu écrits avant | — |
| `usine/outils/` | lots de la session isolée, comparaisons, photo avant/après, nettoyage | `usine/outils/LISEZMOI.md` |
| `runs/*-comprendre/` | **78 lectures** déjà faites (payées ou lues par la session isolée), versionnées ; le reste de `runs/` est jetable | — |
| `etudes/01` à `06` | les preuves d'octobre (pièces, PoC, règles, testeur, compréhension, écrans) | — |
| `anatomie_app.md` | le portrait d'une app bien formée : la cible contre laquelle on juge | — |

**La pile du squelette** : Next.js 16.4.6, React 19, ZenStack 3.9.7, PostgreSQL
(conteneur `temporal-postgresql`), TanStack Query, Tailwind 4, Playwright, avec nos propres pièces d'écran (pas de
bibliothèque de composants).

### 3.2 Hors du dépôt

| Où | Quoi |
|---|---|
| `C:\Users\BAMBARA Arthur\lecteur-isole` | **la boîte aux lettres** : une session Claude Code ouverte à la main, sans connaissance du projet ; chaque question est lue par un agent neuf `lecteur` (lire et écrire seulement) ; qualifiée le 13 oct (5 critères écrits d'avance), 33 briefs lus à 0 $ |
| `C:\Users\BAMBARA Arthur\poc-agents` | apps **A** et **B** construites par un agent du commerce, outils de mesure, juge générique, **sonde** des droits (`outils/sonde/sonde.mts`) |
| `C:\Users\BAMBARA Arthur\poc-a0` | app **A0** construite par l'agent en 1 h 02, avec son contrat technique |
| Base de données | 6 bases gardées pour ces essais : `poc_a`, `poc_a0`, `poc_a_juge`, `poc_b`, `poc_b2`, `poc_mediatheque` |

### 3.3 Ce qui manque (connu)

- un juge d'écrans **indépendant du squelette** (le moteur de parcours) ;
- la sonde générique **pas encore prouvée par sabotage** ;
- la famille de défauts que le juge des règles rate : relire ou **modifier ses propres fiches après avoir perdu son
  rôle** (classement : relire = toléré, **modifier = critique**, à attraper par le juge par modèle) ;
- la boîte, le moteur de l'agent, l'orchestrateur, les traces ;
- la garde de `sur-mesure/`, les migrations de données, le déploiement, les vrais comptes, la porte du miroir
  (réponses du client).

### 3.4 Le ménage du 13 novembre (fait, prouvé)

- **Supprimés** : `poc/` (études d'octobre, conclusions dans `etudes/`), l'ancienne usine `factory-sprint0/`, les docs de
  l'usine 1, 49 apps fabriquées et 114 bases de données (≈ 1,9 Go de fichiers, ≈ 0,9 Go dans la base ; le disque
  virtuel de Docker ne rétrécit qu'après compactage). Tout ce qui
  était suivi par git reste dans son historique (dernier commit avant le ménage : `8d4e288e`).
- **Déménagés dans `usine/`** : le calculateur et son banc, les briefs (apprentissage, examen sans l'ouvrir), la grille et
  les sorties de l'étude 05, le brief de la médiathèque ; la clé `.env` est à la racine du dépôt.
- **Preuve** : banc du calculateur **identique au caractère près** avant et après ; carte des blocs : contrôle OK ;
  chaque chemin lu par la répétition, la mesure des champs et la boîte aux lettres existe ; fabrication de la
  médiathèque identique avant et après (étapes 1 à 7 au vert, même arrêt à l'étape 8, voir la montée de Next.js).
- **Reste à faire par Arthur (administrateur)** : 7 dossiers vides et verrouillés dans `factory-sprint0/` (restes de
  pytest). Dans un PowerShell **administrateur** :
  `takeown /f "C:\Users\BAMBARA Arthur\Desktop\StartupNexus\factory-sprint0" /r /d y ; icacls "C:\Users\BAMBARA Arthur\Desktop\StartupNexus\factory-sprint0" /grant Administrators:F /t ; Remove-Item -Recurse -Force "C:\Users\BAMBARA Arthur\Desktop\StartupNexus\factory-sprint0"`.

---

## 4. Le plan de match

**Comment on travaille (validé le 13 nov, amendé le 19 nov)** : chaque pièce a son **dossier de conception** dans
[`conception/`](conception/LISEZMOI.md). Arthur ne relit pas le code ligne par ligne :
1. L'auteur, l'un des deux agents désigné par Arthur ou proposé dans un fil, décrit la pièce, ses pièges et ses preuves.
2. L'autre agent, le **vérificateur**, relit le dossier avant le code ; Claude en ligne est facultatif.
3. Arthur décide.
4. On développe, la preuve d'abord.
5. L'auteur écrit le compte rendu ; le vérificateur contrôle les preuves, en les rejouant si besoin. Pour un juge,
   la vérification par l'autre fournisseur est obligatoire.

C'est proportionné à la taille de la pièce. Un fil de vérification comporte les positions et trois tours au plus ;
un risque bloquant nouveau peut toujours être signalé à Arthur. Seuls les points bloquants arrêtent le travail. Le
danger est d'aller trop vite et d'empiler de la complexité (l'usine 1 avait 23 000 lignes d'orchestration, et c'est ce
code qui cassait). **Ce sont les preuves qui font foi, pas les avis.**

**Deux agents pairs** *(validé par Arthur le 19 nov, avec les amendements du fil « Arrivée de Codex »)*.
- Claude Code (Anthropic) et Codex (OpenAI) travaillent dans le même dépôt, sous les mêmes règles (`AGENTS.md`).
- **Aucun n'est supérieur.** Ils discutent par écrit dans `dialogue/`, avec d'abord des positions indépendantes, puis
  trois tours d'échange au plus. Ils cherchent un consensus fondé sur des preuves, et rendent une synthèse à Arthur,
  qui tranche.
- Sur chaque pièce, l'un est l'auteur et l'autre le vérificateur : il relit le dossier avant et vérifie les preuves
  après, en les rejouant si besoin. Pour un juge, l'autre fournisseur vérifie obligatoirement.
- Claude en ligne devient facultatif.
- Protocole : [`dialogue/LISEZMOI.md`](dialogue/LISEZMOI.md).

| Étape | La question | La démonstration | Critère d'arrêt |
|---|---|---|---|
| **0. Le poste** | l'usine refabrique-t-elle au vert, sur une pile sans faille connue ? | médiathèque, types et union sportive au vert ; preuves par sabotage identiques | une montée de version qui casse un juge : on s'arrête et on comprend |
| **1. Trois essais jetables** | les trois risques qui peuvent tout changer tiennent-ils ? | un compte rendu par essai, contre des critères écrits avant | une mauvaise nouvelle change le plan avant qu'on construise |
| **2. Le squelette de bout en bout** | toute la chaîne, en version mince, s'emboîte-t-elle ? | **une commande** sur la médiathèque va au bout ; relancée, mêmes verdicts sans repayer ce qui est déjà fait. Un appel extérieur dont la réponse s'est perdue a un **résultat inconnu** : il n'est jamais relancé en silence (précisé le 19 nov) | elle n'emboîte pas : on corrige l'emboîtement avant d'épaissir |
| **3. Qualifier les juges** | peut-on croire les juges qui jugeront l'agent ? | banc de qualification au vert, seuils écrits avant | un juge qui hésite ou rate une famille critique n'est pas utilisé |
| **4. Première capacité** | la recette des capacités marche-t-elle ? | **tableaux de bord** de bout en bout, puis le calendrier | des défauts nouveaux qui ne décroissent pas d'une app à l'autre |
| **5. L'évolution** | peut-on changer une app livrée sans rien perdre ? | une évolution avec perte refusée sans accord ; répétition sur une copie restaurée | une migration qui perd une donnée en silence |
| **6. Le premier vrai client** | l'usine tient-elle face à un vrai besoin ? | miroir lu à deux, app livrée, sauvegarde restaurée | ce qui casse fixe la suite |

### Étape 0 — Le poste

- **Le ménage** : ✔ fait le 13 nov (§3.4).
- **La montée de Next.js (16.4.0 → 16.4.6)** : ✔ faite le 13 nov ([dossier](conception/montee-nextjs.md)).
  - 16.4.0 avait 2 failles critiques et `next build` refusait de construire.
  - 13 paquets sont passés à des versions correctives (Next, zod, hono).
  - L'usine contrôle désormais les failles connues avant de fabriquer : une faille critique arrête la fabrication
    (preuve 3/3).
  - Les trois exemples sont au vert ; les sabotages d'écran sont attrapés à 8/8 ; les règles, à 35/41 avec effet,
    comme en octobre.
  - Restent 4 failles hautes et 1 moyenne, sans correctif, dans les outils de Prisma et de ZenStack.
- **Le compte Claude d'Arthur** (réglage d'entraînement, conditions de l'abonnement) : écarté par Arthur le 14 nov. Ce n'est pas bloquant tant que les briefs sont
  publics ou fictifs et que les vrais clients passent par l'API. Risque accepté (inconnue n° 8) : si les limites de
  l'abonnement gênent, on passe à l'API.

### Étape 1 — Trois essais jetables (hors de l'usine, jetés après)

Les trois apps d'octobre servent de terrain :
- **l'app de l'agent** : un agent du commerce l'a construite depuis notre description ;
- **l'app mixte** : le cœur et les écrans de base viennent de l'usine, plus 4 écrans de l'agent ;
- **l'app du brief seul** : l'agent n'avait que le brief.

| Essai | Ce qu'on fait | Mauvaise nouvelle | Durée max |
|---|---|---|---|
| **[L'essai de la boîte](conception/essai-boite.md)** : un atelier fermé pour l'agent tient-il sur ce PC ? | avec **Docker Desktop**, déjà installé, en cochant son démarrage automatique ; un atelier **sans aucun réseau**, avec sa propre base à l'intérieur ; le cœur de l'app en lecture seule ; 20 cycles, 10 sabotages | pannes, lenteurs ou fuite : d'abord une distribution Linux dédiée, puis un autre ordinateur | 2 jours |
| **[L'essai de l'agent constructeur](conception/essai-agent-constructeur.md)** : Claude Code, enfermé, construit-il assez bien ? | **Claude Code lui-même** est l'artisan, dans une session ouverte par Arthur. Il ne modifie que les écrans, et toutes ses commandes passent par l'atelier. Une petite tâche dans l'app de l'agent, jugée par un test caché | qualité, durée, ou abonnement épuisé (plus d'un quart d'une fenêtre d'usage) : l'artisan passe par l'API | 2 jours |
| **[L'essai du juge d'écrans](conception/essai-juge-ecrans.md)** : un inspecteur sans IA s'y retrouve-t-il ? | des parcours joués par nom visible, sur les trois apps d'octobre ; échecs classés automatiquement ; 5 sabotages | trop d'« introuvable » : le contrat des noms à l'écran passe en premier | 2 jours |

**État au 14 nov** : les trois essais ont été relus deux fois par Claude en ligne, corrigés, et ont reçu le « go »
d'Arthur.
- **L'essai de la boîte** : **la faisabilité est montrée, les refus ne sont pas qualifiés.** Vérification par Codex le
  19 nov, en lecture :
  - l'atelier tourne sur ce poste, et les cycles, la construction et les témoins concordent avec les fichiers bruts ;
  - **onze indicateurs d'échec sont enregistrés ; ils ne démontrent pas tous un refus effectif par la protection, ni
    sa raison** (le script comptait toute erreur comme un refus), et rien ne prouve une seule version. Mon compte rendu
    disait « chacun pour la bonne raison » : c'était trop fort.

  **Décision d'Arthur, le 19 nov : l'atelier sera qualifié dans la chaîne complète** (étape 2), au lieu de refaire un
  banc d'essai maintenant ([fil](dialogue/2026-11-19-verification-essai-boite.md)).
- **L'essai de l'agent constructeur** : prêt ; il demande qu'Arthur ouvre une session.
- **L'essai du juge d'écrans** : **faisable, pas encore admis** (compte rendu réécrit le 17 nov après la relecture et
  un rejeu sur une seule version).
  - **Sans repli, l'inspecteur ne joue aucun parcours autorisé**, sur aucune des trois apps. Avec ses six replis :
    51/51 sur l'app mixte, 38 justes sur 44 jugés sur l'app de l'agent.
  - Les sabotages (5 prévus + 1 de remplacement) sont attrapés à chaque passe, aussi au ralenti. 0 hésitation.
  - Le rejeu a trouvé et corrigé trois défauts de délai, et une fausse alarme.
  - La durée dépasse le seuil : 175 s et 127 s par passage.
  - **Le contrat des noms à l'écran passe en priorité.**
- **Le contrat des noms à l'écran** : [dossier](conception/contrat-noms-ecran.md) écrit le 16 nov, **relu le 16 nov**
  par Claude en ligne et une IA d'un autre fournisseur (OK avec corrections, unanime), corrections intégrées. Taille
  **critique** (relu aussi après). Onze règles (la onzième, « la page dit quand elle a fini de charger », trouvée par
  le rejeu du 17 nov) et 16 sabotages : tout nom qu'un juge cherche vient de la description et
  est montré au miroir. **« Oui » d'Arthur le 19 nov, après vérification du dossier par Codex** (relecteur d'un
  autre fournisseur, qui peut lire le code et rejouer les preuves). Renommé le 19 nov : il s'appelait « contrat
  d'accessibilité ».
- **À venir, après le contrat : l'essai des exemples du client recueillis à l'aveugle** (hypothèse 12, décidé par
  Arthur le 19 nov). [Dossier](conception/essai-exemples-a-l-aveugle.md) écrit le 19 nov, à vérifier par Codex.
  - Sur un brief fictif, une personne qui **ne connaît pas l'usine** joue le client. Arthur la choisit.
  - Elle répond d'abord à quelques questions concrètes tirées des phrases du brief, sans voir notre calcul.
  - Ses réponses sont ensuite comparées à la matrice et à l'app.
  - Une erreur de droit est glissée exprès dans la description : l'essai doit l'attraper. Le miroir seul l'attrape-t-il ?

  Ses seuils s'écrivent dans son dossier, avant l'essai.

L'essai de la boîte et celui du juge d'écrans sont indépendants ; l'essai de l'agent constructeur a besoin de
l'atelier.

**mini-swe-agent attend un budget d'API** (décidé le 14 nov) : nourrir un autre agent avec l'abonnement n'est pas
l'« usage ordinaire de Claude Code » que prévoient les conditions d'Anthropic. Ce qu'on a appris en lisant son code
reste valable pour ce jour-là :
- sa classe de modèle se remplace ;
- il coupe les sorties de plus de 10 000 caractères, par sa configuration ;
- sa boucle tourne hors de l'atelier ;
- il n'a aucune limite d'étapes par défaut.

Inconnue n° 3 fermée.

### Étape 2 — Le squelette de bout en bout (médiathèque)

Une seule commande enchaîne tout, en version minimale :
1. l'image figée ;
2. la boîte ;
3. le moteur derrière la prise unique `construire(tâche, boîte, limites) → résultat` ;
4. **une** tâche d'agent (enrichir un écran de liste) ;
5. les contrôles mécaniques (zones, dépendances, imports interdits, secrets) ;
6. les juges existants et la sonde ;
7. une boucle de correction (2 au plus) ;
8. les événements complets dans une table de traces (noms d'après les conventions OpenTelemetry `gen_ai`), et des
   captures d'écran par les juges.

L'orchestrateur est du code Python seul, sans IA : une table des transitions permises, « écrire avant d'agir », un
verrou PostgreSQL par app, la preuve par coupures (on le tue au hasard, il reprend sans repayer ce qui est déjà fait).
*Précisé le 19 nov, relevé par Codex : un appel extérieur (une IA, plus tard un fournisseur) dont la réponse s'est
perdue a un **résultat inconnu**. On ne le relance jamais en silence. On le rapproche, ou on demande à Arthur, sauf si
le fournisseur garantit qu'une même demande n'est exécutée qu'une fois.*

**L'atelier y devient une pièce qualifiée** (décision d'Arthur, 19 nov, après la vérification de Codex). Son dossier
prévoit :
- des sabotages qualifiés : la raison de chaque refus vérifiée, et un témoin positif par famille ;
- les empreintes, une sortie séparée, des noms de conteneurs propres ;
- la vérification par Codex, qui rejoue les preuves.

Deux hypothèses entrent aussi dans cette étape (décision d'Arthur, 19 nov) :
- **(hypothèse 13) Prouver les chemins d'accès de l'artisan.** Des sabotages : un écran de l'artisan qui importe le
  client de base de données non protégé, écrit du SQL brut, appelle une route sans session, ou ouvre la fiche d'un
  autre par son adresse. Chacun doit être attrapé par les contrôles mécaniques ou par l'inspecteur, avec une identité
  vérifiée.
- **(hypothèse 15) Le « résultat inconnu ».** Un petit essai de coupures sur une doublure locale : avant l'appel,
  pendant, après l'effet, et avant d'enregistrer la réponse. Le résultat attendu de chaque coupure est écrit d'avance.

### Étape 3 — Qualifier les juges et le banc des moteurs

- la **sonde** prouvée par sabotages ;
- le **juge par modèle** (fast-check), qui joue des suites d'actions au hasard et compare la base au modèle ; il doit
  attraper « modifier ses fiches après avoir perdu son rôle » ;
- le **moteur de parcours** détaché du squelette, avec des données d'essai générées depuis la Description ;
- le **banc de qualification** : détection par famille, zéro faux positif sur les témoins, zéro hésitation, vitesse,
  limites écrites. Les seuils sont fixés avant de lancer. **(Hypothèse 14, 19 nov) Chaque juge est qualifié famille
  par famille**, avec des cases séparées :
  - détecté dans la bonne classe ;
  - sabotage sans effet ;
  - survivant ;
  - erreur ;
  - délai dépassé ;
  - non jugé.

  Pour un tirage au hasard, on prouve que la suite critique est rencontrée, au lieu de le supposer ;
- le **banc des moteurs** : 3 ou 4 tâches, chacune jouée plusieurs fois, une partie cachée. Toute modification des
  consignes, du modèle, du moteur ou des outils le repasse ;
- **le vrai juge d'écrans**, admis avec ses propres preuves. Ce que la relecture du 16 nov demande pour lui :
  - un témoin du rejeu pour une **modification** (pas seulement des créations et une confirmation) ;
  - la preuve que la session interdite est bien reconnue par le serveur avant le rejeu (une page qui affiche
    l'identifiant de la personne connectée) ;
  - la preuve de la classe « présent mais inutilisable », avec un témoin proche : un bouton désactivé à bon droit
    (tant qu'un champ obligatoire est vide) ne doit pas être signalé ;
  - des données de départ qui respectent les règles de l'app : préparées par sa couche de données plutôt que par du
    SQL brut, ou vérifiées contre ses invariants ;
  - l'isolement des données si les parcours tournent en parallèle (une base par fil, ou rester l'un après l'autre) ;
  - aucune donnée réelle dans les traces (les « films » contiennent la page, les requêtes et leur contenu) ;
  - des parcours propres, avec leur oracle, pour les écrans riches (recette des capacités) ;
  - **(trouvé par le rejeu du 17 nov) ne dépendre d'aucun délai.** L'inspecteur de l'essai avait trois défauts de
    vitesse qui pouvaient fausser un verdict en silence. Les deux premiers donnaient un faux « interdiction
    respectée » :
    - il notait l'adresse **avant** la fin d'un changement de page (une interdiction était contrôlée à la mauvaise
      adresse) ;
    - il concluait à une **absence** sur une page qui affichait encore « Chargement… » ;
    - sa remise à zéro de la base pouvait attendre sans fin, ou se bloquer.

    Le vrai juge attend que l'adresse change, ne conclut à une absence que sur une page déclarée chargée, et borne
    ses attentes. **Il est prouvé par une passe sur un navigateur ralenti, qui doit donner les mêmes verdicts** ;
  - **(rejeu du 17 nov) ne jamais juger une interdiction à l'aide d'un repli.** Un mouvement de stock reconnu par son
    produit a donné une fausse « interdiction violée » : le lien menait à la page du produit, que le membre a le droit de
    voir ;
  - une clé fixe pour l'empreinte des données de départ (`pg_dump --restrict-key`). Sans elle, PostgreSQL ajoute une clé
    tirée au hasard à chaque export, et l'empreinte ne prouve rien ;
- **l'essai des sabotages proposés par l'IA** (inconnue n° 11, placé ici par Arthur le 16 nov) : l'IA propose des
  sabotages pour l'app mixte sans voir les 6 faits main, on les applique, on compare. Elle propose, une preuve tranche,
  le résultat est figé : jamais dans le verdict. Rien n'en dépend avant : le juge lit un fichier de sabotages, qu'il
  soit écrit à la main ou proposé.

### Étape 4 — Première capacité : les tableaux de bord

Pourquoi elle : la plus demandée dans les vrais briefs (≈ 13 sur 33), elle ne touche pas aux droits en écriture,
elle est presque toute faite par l'agent, et son juge est simple et fiable (recalculer l'agrégat dans la base, avec les
droits du rôle). Ensuite **le calendrier** (11 sur 33), le meilleur exercice pour les juges qui dépendent du temps
(horloge et fuseau figés). Les autres capacités suivent la demande mesurée.

**Grandir sans multiplier les règles** (consensus des deux agents, décision d'Arthur, 19 nov) :
- une bibliothèque éprouvée fait les graphiques, et l'agent leur présentation ;
- la description dit seulement **quoi compter, sur quelles fiches, pour quel rôle** ;
- un juge indépendant recalcule le chiffre avec les mêmes droits.

**On mesure la vitesse de croissance** : sur cette première capacité, puis sur une seconde app fictive qui la
réutilise. On compte :
- le temps de conception, de construction et de qualification ;
- les interventions humaines ;
- les changements ajoutés à la description ;
- les preuves reprises ou créées.

Arthur fixe **avant** le temps disponible et le seuil acceptable, et les échecs sont publiés. **Aucune capacité n'est
admise pour gagner du temps si ses preuves échouent ou manquent.** Pour les tableaux de bord, il faut au minimum :
- des données fictives ;
- un rôle autorisé et un rôle limité ;
- un chiffre attendu, défini indépendamment du graphique ;
- un sabotage qui inclut une fiche interdite.

### Étape 5 — L'évolution

Opérations d'évolution typées, chacune avec sa classe de risque (sans perte, ou avec perte : accord explicite du client
dans le miroir) ; migrations de structure par `zen migrate` (Prisma Migrate), migrations de données écrites par
l'usine ; patron « étendre, migrer, retirer » ; fonctions de mise à niveau des Descriptions ; répétition sur une copie
restaurée de la dernière sauvegarde ; garde de `sur-mesure/`.

**(Hypothèse 16, 19 nov) Vérifier les écritures pendant une évolution.**
- Les témoins vérifient les **valeurs et les droits**, pas seulement le nombre de lignes, y compris pour une écriture
  qui arrive pendant le changement, puis lors d'une panne.
- Un sabotage supprime ou transforme une donnée : le système doit bloquer ou signaler la perte.
- On distingue quatre retours en arrière, qui ne se valent pas :
  - revenir à l'ancien code ;
  - défaire la structure ;
  - restaurer une copie de la base, qui ne garde pas les écritures arrivées depuis ;
  - un effet extérieur, déjà parti.

### Étape 6 — Le premier vrai client

- le miroir v1 : la porte, les réponses du client, lu à deux ;
- les vrais comptes (Better Auth plutôt que Clerk : utilisateurs dans notre base) ;
- l'IA par l'API, pas par l'abonnement ;
- le déploiement d'un seul commit jugé, vérifié par son empreinte ;
- les sauvegardes, restaurées au moins une fois ;
- la surveillance ;
- un examen de sécurité au-delà des droits (`npm audit`, scan OWASP ZAP, en-têtes) ;
- la Loi 25 (évaluation des facteurs relatifs à la vie privée), validée par un juriste ;
- avant tout cela, l'**examen** sur le lot caché, par l'IA du produit, jamais par la boîte aux lettres.

### Ce qu'on ne construit pas encore

- la compression automatique du contexte, tant que la courbe de taille ne la réclame pas ;
- DBOS ou un moteur de flux, tant qu'un seul processus suffit (et plus de Temporal) ;
- gVisor, tant qu'aucune donnée sensible n'est en jeu ;
- toute la chaîne OpenTelemetry : la table de traces suffit ;
- LiteLLM et la mise en cache des consignes, tant qu'on n'est pas sur l'API ;
- Langfuse et la salle de contrôle, avant que le squelette marche ;
- le choix automatique du modèle par tâche ;
- l'anonymisation automatique des demandes, tant que les demandes sont fictives (pour de vrais clients : un outil
  établi, par exemple Microsoft Presidio, pas des expressions régulières maison).

---

## 5. Le registre des inconnues

Chaque inconnue a son essai, sa durée maximale et la décision écrite **avant** de savoir.

| # | Inconnue | L'essai qui tranche | Durée max | Décision écrite d'avance |
|---|---|---|---|---|
| 1 | ~~L'atelier fermé tient-il sur ce PC ?~~ | l'essai de la boîte | 2 jours | **fermée le 14 nov : oui** (20/20 cycles, 0,9 s pour monter et jeter, construction en 35 s, 11 sabotages refusés ; redémarrage du PC vérifié le 16 nov. Chiffres rapportés par Claude Code. **Vérification de Codex le 19 nov, en lecture** : les chiffres de faisabilité concordent avec les fichiers bruts ; **onze indicateurs d'échec enregistrés, qui ne démontrent pas tous un refus effectif ni sa raison** (le script comptait toute erreur comme un refus), et rien ne prouve une seule version. L'atelier sera qualifié dans la chaîne complète ([fil](dialogue/2026-11-19-verification-essai-boite.md))) |
| 2 | Claude Code, enfermé dans l'atelier, construit-il assez bien et assez vite, sans épuiser l'abonnement ? | l'essai de l'agent constructeur | 2 jours | non → l'artisan par l'API, avec un budget par tâche |
| 3 | ~~mini-swe-agent coupe-t-il les sorties longues ?~~ | lecture de son code | 1 h | **fermée le 14 nov : oui**, par sa configuration (au-delà de 10 000 caractères, le début et la fin seulement) |
| 4 | ~~Le juge d'écrans tient-il sur des écrans d'agent ?~~ | l'essai du juge d'écrans | 2 jours | **fermée le 16 nov : faisable, pas encore admis** (reformulé après la relecture). Un inspecteur sans IA peut jouer ces parcours, et certaines interdictions, sur des apps construites différemment, **à condition que les noms soient définis d'avance** : sur nos propres écrans, aucun parcours autorisé n'a réussi sans repli. → **le contrat des noms à l'écran passe en priorité** ; le vrai juge sera admis à l'étape des juges, avec ses propres preuves |
| 5 | Quelle taille de tâche pour l'agent ? | banc des moteurs (étape 3) | — | la plus grosse qui finit sans dépasser le contexte mesuré |
| 6 | Masquer les vieilles sorties suffit-il ? | courbe de taille du contexte (étapes 2 et 3) | — | non → repartir à neuf avec un résumé de l'orchestrateur, avant toute compaction |
| 7 | Le miroir attrape-t-il les erreurs de lecture ? | double lecture comparée (désaccord = question), puis le premier vrai client | — | non → le miroir passe avant les capacités |
| 8 | L'abonnement permet-il un usage d'agent aussi intensif ? | **risque accepté par Arthur (14 nov)** ; mesuré à l'essai de l'agent constructeur | — | limites atteintes ou gênantes → l'agent par l'API |
| 9 | La Loi 25 permet-elle d'envoyer une demande anonymisée à un fournisseur hors Québec ? | un juriste | avant le 1er client | non → modèle local pour ces clients |
| 10 | ~~Next.js 16.4.6 fonctionne-t-il avec ZenStack 3.9.7 ?~~ | la montée de Next.js | ½ jour | **fermée le 13 nov : oui** (3 exemples au vert, preuves par sabotage inchangées) |
| 11 | *(hypothèse du 16 nov, question d'Arthur sur la rigidité ; essai placé à l'étape des juges)* **L'IA peut-elle servir d'articulation souple autour des juges, sans entrer dans le verdict ?** Le motif : elle **propose** (sabotages d'une capacité, missions des écrans riches, carte d'un écran d'agent, explication d'un échec), une **preuve tranche** (programme, ou client au miroir), le résultat est **figé** dans un fichier relu ; ce qui revient souvent devient une règle (registre). Une adaptation sert à juger une interdiction seulement après que le jumeau permis l'a prouvée. Précédents : Meta, tests générés par IA guidés par des défauts inventés (article de 2025) ; Playwright, ses agents de test depuis la version 1.56 (son « réparateur » = juge assoupli en silence : interdit pendant un jugement) | l'IA propose des sabotages pour l'app mixte **sans voir les 6 faits main** (la clé de correction), on les applique, on compare | 1 jour | oui (elle retrouve l'essentiel des familles, peu de propositions fausses) → sabotages et missions des bords proposés par l'IA à chaque nouvelle capacité ; non → faits main pour l'instant |
| 12 | *(hypothèse, regard neuf de Codex, décidée par Arthur le 19 nov)* **Des exemples du client recueillis à l'aveugle attrapent-ils une erreur de compréhension que le miroir laisse passer ?** | l'essai des exemples à l'aveugle (étape 1, après le contrat) : un brief fictif, une erreur de droit glissée exprès, une personne qui ne connaît pas l'usine | ½ journée de préparation, plus le temps du « client » | oui → les exemples entrent dans le miroir ; non → le miroir reste tel quel, et on cherche autre chose pour l'inconnue n° 7 |
| 13 | *(hypothèse, 19 nov)* **Les chemins d'accès de l'artisan aux données sont-ils tous fermés ?** (« il ne peut pas faire fuir » était trop fort) | les sabotages de chemins d'accès (étape 2) | dans l'étape 2 | un chemin ouvert → une garde mécanique ou de base de données avant tout client ; aucun → la garde est prouvée pour ces chemins seulement |
| 14 | *(hypothèse, 19 nov)* **Chaque juge détecte-t-il chaque famille de défauts qu'il annonce ?** | le banc de qualification par familles (étape 3) | dans l'étape 3 | une famille non prouvée → le juge ne l'annonce pas |
| 15 | *(hypothèse, 19 nov)* **Après une panne, l'usine sait-elle dire « résultat inconnu » au lieu de relancer en silence ?** | l'essai de coupures sur une doublure locale (étape 2) | dans l'étape 2 | non → l'orchestrateur n'est pas admis |
| 16 | *(hypothèse, 19 nov)* **Une évolution garde-t-elle les valeurs, les droits et les écritures faites pendant le changement ?** | l'essai d'évolution (étape 5) | dans l'étape 5 | non → pas d'évolution avec données réelles |
| 17 | *(hypothèse, 20 nov : vision d'Arthur, rapportée par Codex ; rien n'est décidé, l'architecture ne change pas)* **L'usine peut-elle se compléter elle-même ?** Face à une demande nouvelle, elle reconnaît ce qui lui manque (elle le fait déjà : refus franc, « pas encore dans notre stock ») ; une IA en atelier construit le code nécessaire, propre à l'app ; ce qui revient et passe ses preuves devient une pièce. Question liée d'Arthur : **pourquoi des pièces plutôt que tout générer ?** Déjà mesuré sur **un seul** brief le 22 oct : l'agent seul (A0) sert les 11 demandes en 1 h et ≈ 7,50 $, avec une faille latente de droits que notre juge a trouvée ; l'usine assemble en quelques minutes, sans IA, des droits prouvés, et une correction vaut pour toutes les apps (`archives/USINE_avant_plan_2026-11-13.md` §0.10, points 12 à 16). Le point dur n'est pas d'écrire le code, c'est d'écrire **le juge** d'une capacité inconnue sans que le constructeur soit juge et partie | *proposé par Claude Code, à placer par Arthur* : (a) à l'étape des juges, une fois le juge du contrat et la sonde qualifiés, rejouer « agent seul contre usine » sur plusieurs briefs, défauts comptés par les juges ; (b) à la première capacité (étape 4), mesurer quelle part du dossier de capacité deux IA de fournisseurs différents produisent seules, et combien de défauts la vérification croisée attrape | (a) ½ jour par brief ; (b) dans l'étape 4 | *à écrire avec Arthur avant l'essai.* Proposition : (a) si l'agent seul atteint la même qualité jugée sur les droits, à coût acceptable → la frontière entre pièces et génération se déplace, les pièces ne restent que là où un juge ne voit pas ; sinon → pièces pour le cœur. (b) si la boucle « une IA construit, l'autre juge, Arthur dit go » tient sur une capacité → on retire le go d'Arthur seulement pour les capacités sans droits ni argent ; sinon → la boucle reste manuelle |

---

## 6. Les doctrines (le traducteur les applique toujours)

| Doctrine | Contenu |
|---|---|
| Natures | **profil** (un par acteur) · **catalogue** (référentiel visible des connectés) · **registre** (tenu par l'équipe, visible de ceux qui le tiennent) · **collection** (les éléments d'un acteur) · **enfant** (lignes d'un parent). Circuit permis sur collection et registre |
| Supprimer | jamais par défaut ; seulement si le brief le dit |
| Responsable | le responsable voit en lecture tous les registres ; le client peut le refuser |
| Rôles listés | « connecté » = la liste des rôles déclarés, jamais « toute personne connectée » |
| Clôture | on ne désigne que ce qu'on voit, à la création et à la modification ; on ne re-désigne qu'une fiche vue directement ; on voit ce qu'on modifie |
| Cohérence | deux fiches liées du même rôle propriétaire appartiennent à la même personne |
| Propriétaire immuable | le propriétaire d'une fiche ne change jamais |
| Une étape ne change que l'état | les autres champs restent identiques pendant une transition |
| Prudence | un accès que le brief limite n'est pas élargi |
| Visiteur | un droit sans compte seulement sur une fiche déclarée publique |
| Refus explicites | ZenStack peut répondre « refusé » après avoir écrit : chaque interdiction est une règle explicite |
| Listes de valeurs | liste fixe citée par le brief → champ **choix** ; liste que le client fait vivre → **catalogue** |
| Intégrité | on ne supprime pas une fiche désignée ; seule exception : supprimer un parent supprime ses lignes |
| Variantes | une variante proposée à la place d'une demande refusée ne fait que **retirer**, jamais élargir |

**Pièges techniques connus** : ZenStack 3.9.7 échoue en SQL quand on compare un état ou un choix à sa valeur d'avant
(on écrit valeur par valeur) ; Prisma interdit à une IA de remettre une base à zéro (base neuve à chaque essai) ;
Next.js 16.4 exige la lecture de session derrière un `<Suspense>` ; une action qui change l'état est un formulaire POST,
jamais un lien (Next précharge les liens).

---

## 7. Le registre des corrections

Les corrections n° 1 à 59 sont dans l'ancien document (§7). Bilan : **59 corrections, 0 propre à un brief, 0 juge
assoupli**. La convergence a décru : 4 défauts par app nouvelle au début, puis 0,19 sur le corpus complet.

| # | Date | Correction | Nature | Trouvée par | Générale ? | Juge |
|---|---|---|---|---|---|---|
| 60 | 13 nov | Next.js 16.4.0 vulnérable (2 critiques, 1 haute) : toute fabrication s'arrêtait à la construction. Next a sa propre garde, mais pas les autres bibliothèques (zod, hono avaient aussi des failles) → montée en 16.4.6 et versions correctives ; **l'étape 5 audite le fichier de verrouillage avant d'installer** (`npm audit`) : une faille critique arrête la fabrication, une haute est inscrite au rapport, sans réseau « non fait » (jamais un « accepté » silencieux). Preuve `python -m usine.preuve_audit` 3/3 ; 3 exemples au vert ; sabotages d'écran 8/8 ; règles 35/41 avec effet (identique à octobre) | dépendance vulnérable ; l'usine ne surveillait pas ses propres dépendances | `next build` (fabrication de contrôle du ménage) | oui | nouveau contrôle (prouvé) |
| 61 | 16 nov | **Les noms des boutons ne passent pas par le miroir, et le bouton de création n'a pas de nom dans la description.** *(Diagnostic corrigé le 16 nov au soir. J'avais écrit « le verbe de création validé n'est jamais affiché » ; c'était faux sur deux points : le « verbe de création » de la description nomme le bouton de création **en un clic** depuis une fiche liée (« Emprunter » sur un livre), pas le bouton du formulaire ; et le miroir ne montre **aucun** nom de bouton, donc le client ne valide rien.)* Le bouton du formulaire est fabriqué par une règle de grammaire dans `usine/traduire/ecran.py` (« Nouveau / Nouvel / Nouvelle + nom »), fausse devant un h aspiré (« Nouvel hangar »). Un juge extérieur ne peut pas tirer ce nom de la source validée. **À corriger** avec le contrat des noms à l'écran ([dossier](conception/contrat-noms-ecran.md)). **20 nov : corrigé EN PARTIE** : le nom du bouton de création est désormais dans la description (`creation`, format 2), et le traducteur le lit ; la règle de grammaire ne sert plus qu'à proposer un nom avant le miroir. **Reste** : le montrer au miroir (morceau 4) | défaut de l'usine (noms d'écran hors de la description et hors du miroir) | l'inspecteur d'écrans (essai) | oui | — (le juge du contrat, de Codex, en construction) |
| 62 | 16 nov | **Les boutons de connexion simulée du squelette ne portent pas l'identifiant de la personne** (« personne 1 », pas « gerant_1 ») : un juge extérieur ne peut pas se connecter par le nom. **À corriger** avec le contrat des noms à l'écran ([dossier](conception/contrat-noms-ecran.md)). **20 nov : corrigé dans le squelette** : « personne 1 · adherent_1 ». Témoins de l'usine identiques ; le juge du contrat (Codex) le jugera | défaut de l'usine (squelette) | l'inspecteur d'écrans (essai) | oui | — (le juge du contrat, de Codex, en construction) |
| 63 | 19 nov | **Un texte « obligatoire » est enregistré vide** — **confirmé [rejoué] le 19 nov** : par le client protégé de l'app, 34 écritures vides ou faites d'espaces sur 34 ont été ENREGISTRÉES (texte court, texte long, téléphone, e-mail ; création et modification ; les types et la médiathèque fabriqués le 19 nov ; essai `C:\Users\BAMBARA Arthur\essais\contrat-noms\essai-obligatoire.mts`, résultats `defaut-63-*.json`). Le formulaire du squelette retire les espaces, puis transmet une chaîne vide (`usine/modele-app/components/vues.tsx:89-92`). Le contrôle du navigateur (`required`) laisse passer une saisie faite seulement d'espaces, et aucun contrôle côté serveur n'impose « non vide ». Origine lue : le formulaire retire les espaces puis transmet une chaîne vide, et le serveur ne contrôle rien. **À corriger** avec le contrat des noms à l'écran : le serveur refuse un texte obligatoire vide ou fait d'espaces, pour tous les champs, prouvé par un appel direct ([dossier](conception/contrat-noms-ecran.md), morceau 12). **20 nov : corrigé à la source** (`usine/traduire/schema.py`) : chaque champ obligatoire qui est un texte dans la base reçoit `@trim @length(1)`, les outils de ZenStack, **dans cet ordre** (ZenStack les applique dans l'ordre écrit). Preuve [rejoué, par l'auteur ; à vérifier par Codex] sur l'exemple dédié `usine/exemples/textes-obligatoires.json`, avec le même script avant et après : **avant, 0 refusé sur 20 ; après, 20 refusés sur 20**, tous comme entrée invalide nommant le champ, la table inchangée ; témoins 33/33 (valeurs normales et facultatifs vides acceptés, aucun texte vide au départ) ; `updateMany`, `upsert`, `createMany` aussi refusés (30/30). L'essai du 19 nov rejoué : **les 34 écritures alors enregistrées sont refusées, les 34**. Témoins de l'usine identiques (règles et écrans des trois exemples ; failles 3/3 ; règles cassées exprès : les 57 mutants identiques au 13 nov ; sabotages d'écran 8/8). Changement déclaré : les espaces autour d'un texte obligatoire sont retirés à l'enregistrement. Non couvert : l'accès direct à la base (SQL) | défaut de l'usine (squelette et schéma ; le sens de « obligatoire ») | Codex, à la vérification du dossier (lecture du code) | oui | preuve dédiée (20 cas), à rejouer par Codex |

---

## 8. Journal

| Date | Décision | Pourquoi |
|---|---|---|
| 13 nov 2026 | **Concept validé** : usine hybride, inspecteur au centre ; trois zones ; l'agent ne crée aucune table ; les juges cochent les tâches | les recherches de novembre (archivées) |
| 13 nov 2026 | **Moteur de l'agent** : option 1 (boîte aux lettres) d'abord, option 2 en secours, l'API pour les vrais clients ; première capacité : les tableaux de bord ; sabotage manqué : relire toléré, modifier critique | recommandations acceptées par Arthur |
| 13 nov 2026 | **Ménage du dépôt et nouveau plan** (§3.4) | ne garder que ce dont on a besoin avant de développer |
| 13 nov 2026 | **Méthode : un dossier de conception par pièce** (`conception/`), relu par un relecteur extérieur avant de développer ; proportionné ; un seul tour ; les preuves font foi | proposé par Arthur : comprendre et garder la main sans relire le code ligne par ligne |
| 13 nov 2026 | **La montée de Next.js faite** : 16.4.6, contrôle des failles avant de fabriquer (registre n° 60) | `next build` bloquait toute fabrication |
| 14 nov 2026 | **L'artisan est Claude Code lui-même**, enfermé dans l'atelier ; mini-swe-agent attend l'API ; la boîte aux lettres des lecteurs reste à petit volume | relecture des essais : nourrir un autre agent avec l'abonnement sort de l'« usage ordinaire » prévu par les conditions (vérifié sur la page officielle) |
| 14 nov 2026 | **L'atelier tourne dans Docker Desktop**, avec son démarrage automatique coché, et sans aucun réseau ; la distribution Linux dédiée passe en repli | la panne « Docker ne redémarre pas » n'était qu'un réglage désactivé : moins de pièces, moins de pannes |
| 14 nov 2026 | **L'essai de la boîte est réussi** : l'atelier (Docker Desktop, sans réseau, base dedans, app en lecture seule) tient sur ce PC. Démarrage automatique de Docker activé ; mises à jour figées ; base de l'usine en redémarrage automatique | les seuils écrits d'avance sont atteints, **sauf un relevé incomplet** : la taille du disque avant les images n'a pas été notée ([compte rendu](conception/essai-boite.md)). *Corrigé le 19 nov : j'avais écrit « tous atteints » ; relevé par Codex* |
| 16 nov 2026 | **⚠ Ligne corrigée le 17 nov : l'essai est « faisable, pas admis », avec 0/51 sans repli (voir la ligne du 17 nov). Texte d'origine, gardé pour l'histoire :** L'essai du juge d'écrans est réussi : l'inspecteur sans IA tient (51/51 sur nos écrans avec replis déclarés, 6/6 sabotages dans la bonne classe, rejeu prouvé, 0 hésitation). **Le contrat d'accessibilité devient prioritaire**, avant la chaîne complète ; corrections n° 61 et 62 à faire avec lui | les seuils et la décision écrits d'avance ([compte rendu](conception/essai-juge-ecrans.md)) |
| 20 nov 2026 | **Codex devient aussi une force de développement** : sur le contrat des noms à l'écran, la coupure passe entre le constructeur et le juge. Claude Code construit le côté usine ; Codex construit le juge (l'inspecteur sans repli, sa maquette, ses sabotages) et devient responsable de l'inventaire. Chacun vérifie l'autre. Deux stylos sur des périmètres séparés | demandé par Arthur : « ne pas te laisser tout faire » ; celui qui construit ne doit pas écrire son propre juge ([fil](dialogue/2026-11-20-juge-du-contrat-par-codex.md)) |
| 19 nov 2026 | **Décisions d'Arthur (« oui à tout »)** : (1) le protocole à deux agents est validé, et Codex applique lui-même ses amendements ; (2) le contrat devient « le contrat des noms à l'écran » ; (3) Codex vérifiera l'essai de la boîte, après l'examen des accès ; (4) le `.env` sort du dépôt (les clés se lisent désormais hors du dépôt, `~/.secrets/startupnexus.env`) ; (5) les cinq hypothèses entrent au plan (inconnues n° 12 à 16) ; (6) l'essai des exemples à l'aveugle se fera après le contrat ; (7) la vitesse de croissance sera mesurée à l'étape 4. Le contrat est vérifié par Codex avant d'être développé | fils [Arrivée de Codex](dialogue/2026-11-19-arrivee-de-codex.md) et [Regard neuf](dialogue/2026-11-19-regard-neuf-sur-le-concept.md), en consensus |
| 19 nov 2026 | **Regard neuf de Codex sur le concept** (recherche web, [rapport](dialogue/recherches/2026-11-19-concept-codex.md)) : **on garde le concept hybride.** Cinq hypothèses en discussion : (1) les exemples du client recueillis à l'aveugle avant le miroir ; (2) prouver les chemins d'accès de l'agent ; (3) qualifier les juges par familles de défauts ; (4) le « résultat inconnu » après une panne ; (5) vérifier les écritures pendant une évolution. Trois formulations trop fortes corrigées (« ne peut pas faire fuir », « sans rien repayer », « par construction ») | demandé par Arthur ; à inscrire au registre des inconnues après sa décision ([fil](dialogue/2026-11-19-regard-neuf-sur-le-concept.md)) |
| 19 nov 2026 | **Codex rejoint le travail, comme pair de Claude Code** (proposition, en discussion) : des règles communes (`AGENTS.md`, que `CLAUDE.md` importe), un dialogue écrit et visible (`dialogue/`), aucun agent supérieur, des consensus fondés sur des preuves, Arthur tranche. Premier fil : « Arrivée de Codex » | demandé par Arthur : une autre intelligence, d'un autre fournisseur, pour discuter et parvenir à des consensus |
| 17 nov 2026 | **Rejeu de l'essai du juge d'écrans sur une seule version** (avec empreintes, un passage sans aucun repli, un passage ralenti) : sans repli, aucun parcours autorisé ne passe ; trois défauts de délai de l'inspecteur trouvés et corrigés (deux pouvaient donner un faux « interdiction respectée ») ; une fausse alarme due à un repli. Compte rendu réécrit, chiffre strict en tête. Nouvelle règle d'écriture des comptes rendus (`conception/MODELE-DOSSIER.md` §11 et §11 bis) | Arthur : « sans relecture, on aurait construit l'usine sur des affirmations fausses » |
| 16 nov 2026 | **Relecture du contrat d'accessibilité et du compte rendu du juge d'écrans** par deux IA (Claude en ligne et un autre fournisseur) : le contrat passe à OK avec corrections (dix règles, taille critique) ; l'essai du juge d'écrans prouve une faisabilité, pas une admission ; il est **rejoué sur une seule version**, avec empreintes et un passage sans aucun repli. Deux règles des juges ajoutées (§2.3 : empreintes, refus de juger) | relecture archivée (`archives/echanges-2026-11/relecture-contrat-et-juge-ecrans-2026-11-16.md`) ; « go » d'Arthur pour le rejeu et la mise à jour du plan |
| 16 nov 2026 | **L'IA comme articulation souple, jamais dans le verdict** : elle propose, une preuve tranche, le résultat est figé ; ce qui revient souvent devient une règle. Hypothèse (inconnue n° 11), essai placé à l'étape des juges | question d'Arthur sur la rigidité des scripts et des règles fixes |
| 14 nov 2026 | **Des noms, pas des codes ; des mots simples ; toujours le « pourquoi »** (dossiers renommés, section « En mots simples » en tête de chaque dossier) | demandé par Arthur : les codes et le jargon gênaient sa compréhension |
