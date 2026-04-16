Diagnostic Architectural — Software Agent Factory
Je vais analyser couche par couche, en distinguant ce qui est bien conçu de ce qui génère de la complexité inutile.

1. Le Pipeline Architect — 5 LLM en série

brief_normalizer → retrieval → planner → spec_writer → formatter
Problème fondamental : la perte d'information en cascade
Chaque nœud LLM reçoit l'output du précédent. Chaque transition est une opportunité de perdre une entité. On a un brief qui dit "Product, Order, /acheteur, /dashboard" — ces entités doivent traverser 4 LLM sans jamais être perdues. C'est structurellement fragile.

Ce qu'on a fait pour compenser :

Spec Validator + correction loop (2 re-invokes si DEGRADED)
_is_generic_plan detection dans planner
Requirements[] déterministes depuis parser (bonne idée, mais arrive trop tard dans la chaîne)
Ce qui est réellement nécessaire :

Le brief_parser extrait déjà tout déterministiquement. Les requirements[] sont déjà corrects. La seule valeur ajoutée des LLM dans cet pipeline est :

Planner : structure l'app (pages protégées, auth, types)
Spec_writer : génère la prose technique de la spec + structure Prisma
Formatter : extrait le JSON structuré
Le brief_normalizer et le retrieval servent le spec_writer. Mais 5 nœuds pour arriver à "écris une spec pour cette app" est excessif.

Nœuds de complexité identifiés :

Nœud	Utilité réelle	Problème
brief_normalizer	Normalisait le brief pour RAG query	LLM inutile si parser fonctionne — déjà partiellement supprimé
retrieval	RAG query → standards	Utile, mais query basée sur brief souvent vide (réglé)
planner	Structure JSON de l'app	Rate des pages, génère des plans génériques — output non vérifié
spec_writer	Génère la spec prose	Reçoit le plan (potentiellement incomplet) comme source principale
formatter	Extrait IR JSON depuis spec	Un nœud entier pour parser un output LLM
Le vrai problème du pipeline : le planner génère un plan JSON qui devient la "source de vérité" du spec_writer — mais ce plan n'est pas validé. Les requirements[] déterministes arrivent comme note de bas de page, pas comme structure principale.

2. Le Dev Agent — Complexité stratifiée
Architecture actuelle (après Phase 1)

dev.py (409 lignes)
  └── run_dev_loop() [dev_loop.py ~800 lignes]
        ├── PreBuildValidator [pre_build_validator.py]
        ├── FileSupervisionLoop [file_supervision_loop.py]
        ├── RunStateComputer [build_state_manager.py]
        ├── supervision_manager.py
        │     ├── _supervise_file_inline (tsc + 3 LLM supervisors)
        │     └── run_pre_build_deterministic_checks
        ├── dev_path_utils.py
        ├── dev_reflection.py
        └── dev_compat.py / dev_file_ops.py
~2500 lignes de code pour "un LLM qui écrit des fichiers."

Les nœuds de complexité spécifiques
A — Les 3 superviseurs LLM par fichier (conformity, security, architecture)

Chaque fichier généré passe par 3 appels LLM supplémentaires. Ces superviseurs :

Ont un seuil de correction à confidence > 0.7
Peuvent déclencher une réécriture
Tournent en parallèle mais multiplient les tokens consommés
Le problème : un bon prompt système pour le dev agent devrait déjà inclure les contraintes de sécurité, conformité et architecture. Si le LLM les respecte d'emblée, les superviseurs ne servent à rien. Si le LLM ne les respecte pas, les superviseurs ne sont qu'un deuxième LLM qui espère corriger ce que le premier a raté — sans garantie.

B — Le PreBuildValidator avec content guards

Le PreBuildValidator vérifie avant chaque build :

Supervision loop (corrections en attente)
Blueprint Validator (fichiers obligatoires présents)
Path Guards (conventions nommage App Router)
Forbidden Paths (pages/ interdit)
Forbidden Imports (tokens interdits)
Content Guards (regex/AST config-driven)
Certaines de ces vérifications sont légitimes (blueprint — fichiers obligatoires). Mais les forbidden imports et content guards compensent des dérives LLM qui devraient être réglées dans le prompt système ou les standards Qdrant.

C — active_blocker avec 5 états


blocker = "file_missing::prisma/schema.prisma"
blocker = f"requirements::{prisma_unmet[0]}"
blocker = f"file_missing::{missing_files[0]}"
blocker = f"structural::{structural_gid}"
blocker = "build_error"
blocker = "ready_for_build"
Chaque itération de la boucle calcule un blocker et l'injecte dans le prochain prompt LLM. Le LLM reçoit donc un état de supervision complexe à chaque tour. C'est intelligent sur le papier, mais ça rend le comportement du système difficile à prédire et à débugger.

D — scaffold_extends, templated_names, llm_required_files

Trois catégories de fichiers distincts qui ont des règles différentes pour le LLM. La logique de séparation (templates / scaffold_extends / fichiers LLM) est correcte mais génère une complexité d'orchestration élevée (plus de 50 lignes de setup dans dev.py avant d'arriver à la boucle).

3. Le Système de Standards Qdrant — La source de vérité silencieuse
53 standards dans Qdrant, 14 zones. Le RAG injecte des standards dans l'architect et potentiellement dans le dev agent. C'est une bonne architecture en principe — les standards comme mémoire externe.

Problème : quand les runs échouent (3/3 dans les logs), on ne sait pas si les standards RAG ont contribué à la dérive ou l'ont corrigée. Le système est opaque. Un standard mal rédigé dans Qdrant peut silencieusement dégrader tous les runs sans qu'aucun log ne le montre.

4. La Correction Loop dans architect_activity — Le symptôme vs la cause

for attempt in range(1, MAX_SPEC_CORRECTION_ATTEMPTS + 1):
    spec_validation = validate_spec_requirements(...)
    if DEGRADED → re-invoke architect_agent avec corrective_phrase
    if still DEGRADED after 2 → ApplicationError("SPEC_DEGRADED_UNRECOVERABLE")
Cette loop fait ce que le spec_writer aurait dû faire correctement au premier appel. Elle re-exécute toute la chaîne architect (5 nœuds) pour corriger ce qu'un seul nœud (spec_writer) a raté.

Résultat observé dans les logs : la correction loop re-invoque l'architect, qui re-passe par le même brief_normalizer → même planner → même spec_writer → même DEGRADED. La loop ne peut pas corriger une dérive structurelle dans le pipeline.

Synthèse — Ce qui bloque vs ce qui fonctionne
Ce qui fonctionne bien
brief_parser : extraction déterministe, source de vérité fiable
requirements[] : construits depuis le parser, corrects à 100%
run_build() : exécution réelle du build, feedback concret
Stack-as-Config (nextjs-clerk-prisma.json) : bonne séparation config/code
Temporal : orchestration workflow robuste, retry policy
active_blocker concept : orienter le LLM vers le problème suivant est une bonne idée
Ce qui génère de la complexité sans valeur proportionnelle
5 nœuds LLM en série dans l'architect pour une seule tâche
3 superviseurs LLM par fichier qui corrigent ce que le prompt devrait prévenir
Correction loop architect qui re-exécute tout le pipeline pour corriger un seul nœud
PreBuildValidator content guards qui compensent des dérives de prompt
FileSupervisionLoop avec max_attempts, pending_paths, needs_reverification — machinerie pour gérer l'état de supervision
build_normalized_brief_from_parsed + LLM brief_normalizer + brief_parser — 3 façons d'extraire les mêmes données
La Refactorisation Proposée
Principe directeur
Un LLM bien prompté dans une structure claire n'a pas besoin de superviseurs, de correction loops, ou de 4 nœuds préparatoires. Il a besoin d'un input complet, clair, structuré, et d'un seul objectif à la fois.

Architect — Passer de 5 nœuds à 2
Actuel : brief_normalizer → retrieval → planner → spec_writer → formatter

Proposé :


parser (déterministe) → spec_builder (1 LLM)
parser : brief_parser actuel — extrait pages, routes, modèles → produit requirements[]
retrieval : RAG sur raw_phrase ou premiers 200 chars du brief (pas sur brief normalisé)
spec_builder : 1 seul LLM reçoit requirements[] + raw_phrase + RAG → génère spec + plan intégré
Gain : 3 LLM supprimés, 0 perte d'information en cascade, requirements toujours respectés car ils sont l'input principal (pas un appendice).

Dev Agent — Supprimer les superviseurs LLM, renforcer le prompt
Actuel : LLM génère → 3 superviseurs LLM relisent → correction → LLM réécrit

Proposé : 1 seul LLM dev agent avec prompt système complet (sécurité, conformité, architecture injectés). Si le fichier a des erreurs tsc/eslint (déterministe), le résultat est injecté directement dans le prochain tour de boucle sans appel LLM supplémentaire.

Gain : 3 superviseurs LLM supprimés, coût token divisé par ~4 par fichier.

La Correction Loop — La supprimer
Au lieu de re-invoquer tout le pipeline architect quand la spec est DEGRADED, la spec ne peut pas être DEGRADED si les requirements sont l'input principal (pas un appendice). La correction loop devient inutile.

Principe de calibrage LLM
Ce que le LLM doit toujours avoir clairement :

L'objectif exact (pas "écris une spec générique", mais "écris une spec qui couvre exactement ces requirements")
Les contraintes (stack, patterns d'implémentation via RAG)
L'état actuel (ce qui existe déjà, ce qui manque)
Le résultat attendu (format de sortie explicite)
Ce que le LLM ne devrait jamais avoir à "deviner" parce que ce n'est pas dans son input :

Quels modèles Prisma créer (déjà dans requirements[])
Quelles pages créer (déjà dans requirements[])
Quelles routes créer (déjà dans requirements[])
En pratique — Ce qui devrait être fait
Architect : fusionner planner + spec_writer en 1 seul nœud, requirements[] comme input primaire
Dev Agent : supprimer les 3 superviseurs LLM, garder uniquement les checks déterministes (tsc/eslint)
Correction loop architect_activity : supprimer quand le pipeline amont est fiable
PreBuildValidator content guards : remplacer par prompt renforcé côté dev agent
FileSupervisionLoop : simplifier si superviseurs LLM supprimés
Ce qui ne change pas :

brief_parser (déterministe, fiable)
requirements[] depuis parser
Temporal workflow structure
Stack-as-Config JSON
run_build() + tsc/eslint déterministe



Le problème RAG — Précision
Le RAG fait deux choses dans ce pipeline :

Dans l'architect : injecté dans le spec_writer pour donner des patterns d'implémentation stack (comment structurer un schema Prisma, comment configurer Clerk, etc.)

Dans le dev agent : le LLM appelle rag_search comme tool pour chercher des patterns techniques pendant la génération de fichiers.

Le risque de dérive est différent dans les deux cas.

Cas 1 — RAG dans l'architect (le plus dangereux)
Un standard dans Qdrant qui dit, par exemple :


"Pour un blog, le modèle principal est Post avec title, content, authorId"
Si ce standard est récupéré pour un brief "marketplace avec Product et Order", le spec_writer reçoit dans son contexte à la fois "Product" (depuis requirements) et "Post" (depuis le RAG). gpt-4o-mini peut dériver vers "Post" parce que c'est dans un exemple structuré du contexte.

Le prompt dit explicitement "le RAG n'apporte que la connaissance stack, pas le domaine métier" — mais si les standards contiennent des noms d'entités concrètes, le LLM ne peut pas faire la distinction. L'instruction dit une chose, le contenu en fait une autre.

Ce qui rend ça opaque : la query RAG dépend du brief normalisé (variable), donc les standards récupérés changent d'un run à l'autre. Un run peut échouer à cause d'un standard qui score 0.41 sur une query et en pollue le contexte — impossible à détecter sans logguer le contenu des standards récupérés.

Cas 2 — RAG dans le dev agent (moins risqué)
Ici le LLM choisit quand appeler rag_search et quelle query utiliser. C'est mieux car c'est explicite. Mais si les standards contiennent du code avec des noms d'entités concrètes (ex: const posts = await prisma.post.findMany()), le LLM peut copier le pattern avec le nom d'entité de l'exemple au lieu du sien.

Solution proposée — Trois axes
Axe 1 : Purger les entités concrètes des standards
Tous les standards qui contiennent des noms d'entités spécifiques (Post, User, Task, Book, Todo) doivent utiliser des placeholders :


❌ "model Post { title String, content String }"
✅ "model <Entity> { <field> <Type>, ... }"
C'est un audit des 53 standards existants — probablement 20-30% contiennent des noms concrets aujourd'hui.

Axe 2 : Rendre le RAG de l'architect statique
Dans la nouvelle architecture (architect simplifié à 2 nœuds), les patterns stack ne changent pas selon le brief. Un middleware.ts pour Clerk s'écrit toujours pareil. Un prisma.config.ts pour Prisma 7 aussi.

Proposition : remplacer le RAG dynamique dans l'architect par un bloc statique injecté dans le system prompt — les 8-10 patterns techniques les plus importants, toujours présents, jamais variables. Zéro cosine similarity, zéro variabilité, zéro dérive cachée.

Le RAG dynamique redevient utile seulement si le brief est très inhabituel et nécessite des patterns spécifiques — cas marginal.

Axe 3 : Traçabilité des standards récupérés
Dans l'immédiat (avant la refactorisation), ajouter dans les metadata du run les IDs et scores des standards récupérés :


"rag_standards_used": [
  {"id": "ZONE_3_001", "score": 0.82, "title": "Prisma schema pattern"},
  {"id": "ZONE_7_002", "score": 0.63, "title": "Clerk middleware"}
]
Quand un run échoue, on peut corréler avec les standards récupérés et identifier lequel a pollué le contexte. Actuellement on ne peut pas faire ce diagnostic.

Ce qui change dans le plan global
Composant	Avant	Après
RAG architect	Dynamique, 10 standards variables	Statique, 8-10 patterns dans system prompt
RAG dev agent	Dynamique via tool	Dynamique mais standards purgés de noms concrets
Standards Qdrant	53 standards, noms concrets possibles	~20 standards techniques purs, placeholders uniquement
Traçabilité	Log count seulement	Log ID + score + titre pour chaque run
L'objectif : le RAG ne doit jamais introduire du contenu métier dans le contexte LLM. Il injecte uniquement de la connaissance stack (syntaxe, patterns, configuration). La séparation domaine/stack qui est déjà dans le prompt comme instruction doit être garantie structurellement par le contenu des standards.


Analyse Complète — Tous les Composants
1. Le Stack Config JSON — nextjs-clerk-prisma.json (574 lignes)
C'est le fichier le plus révélateur du problème systémique. Il a grossi à chaque dérive LLM détectée.

Ce qui est bien :

packages / dev_packages — versions épinglées, excellente idée
templated_files — 13 fichiers pré-écrits sans LLM, c'est exactement la bonne approche
blueprint.required_files — liste claire de ce qui doit exister
env_validation — validation déterministe des env vars
compatibility_matrix — documente les incompatibilités connues
Les nœuds de complexité :

Duplication des règles à 4 endroits différents. La règle "ne pas utiliser bcrypt" existe dans :

forbidden_imports[]
forbidden_auth_patterns[]
spec_validation.forbidden_keywords[]
prompt_rules.auth_rules[]
Quand une règle est en 4 endroits, on ne sait plus laquelle est authoritative. Mettre à jour une règle signifie mettre à jour 4 listes. Et si elles divergent, le comportement devient imprévisible.

import_remaps — un sanitizer déguisé :


"source_fixes": {
  "@clerk/nextjs/api": "@clerk/nextjs/server",
  "auth().protect()": "await auth.protect()",
  "clerkMiddleware } from '@clerk/nextjs'": "clerkMiddleware } from '@clerk/nextjs/server'"
}
C'est un find-replace silencieux sur l'output LLM. Si les règles rules_dev.md sont claires et que le LLM respecte les imports corrects, ce sanitizer est inutile. S'il est nécessaire, c'est que les règles ne sont pas assez efficaces — et le sanitizer masque ça.

9 mandatory_rag_queries exécutées à chaque run :


"versions exactes next.js clerk prisma jest ts-jest..."
"clerk v6 ClerkProvider layout.tsx clerkMiddleware..."
"prisma 7 schema.prisma prisma.config.ts..."
9 × 3 = 27 standards récupérés et injectés dans le contexte de chaque run, quelle que soit l'app générée. Ces 9 queries couvrent des règles stack invariantes (toujours vraies pour nextjs-clerk-prisma). Si elles sont invariantes, elles appartiennent au system prompt statique, pas au RAG dynamique. Le RAG dynamique est fait pour le contexte variable (patterns spécifiques au projet). Ces 27 standards alourdissent le contexte sans valeur ajoutée variable.

6 content_guards qui dupliquent les prompt rules :

Guard	Règle déjà dans
use_client	rules_dev.md règle 5
authorid_requires_userid_guard	rules_dev.md règle 3
prisma_import_path	rules_dev.md règle 2
prisma_named_import	rules_dev.md règle 2
prisma_schema_datasource_url	prompt_rules.orm_rules
route_handler_untyped_signature	rules_dev.md règle 3
Chaque guard existe parce que la règle dans le prompt n'était pas suffisante. Mais ajouter un guard ne rend pas la règle plus efficace — ça crée juste une détection post-génération supplémentaire.

spec_validation.required_sections — rigidité fragile :


"## vue d'ensemble", "## stack technique", "## structure des pages"...
Si la spec LLM écrit "## Pages" au lieu de "## structure des pages", la validation échoue et déclenche une réécriture. C'est du formatage, pas de la qualité. Une règle de structure fragile qui déclenche des LLM calls inutiles.

2. Les Templates — Ce qui est bien et ce qui manque
Ce qui est bien :
Les 13 fichiers templates sont la meilleure décision architecturale du projet. middleware.ts, package.json, layout.tsx, lib/prisma.ts sont identiques pour chaque app — les pré-écrire élimine toute dérive sur ces fichiers critiques.

Ce qui manque :
prisma/schema.prisma est dans scaffold_extends — il est pré-écrit comme template mais le LLM doit le "compléter" avec les modèles. C'est le bon principe mais la mécanique scaffold_extends + locked_until_keyword ajoute de la complexité. La règle simple serait : "le template fournit le datasource/generator, le LLM écrit UNIQUEMENT les blocs model".

3. Les Prompts — L'architecture à deux niveaux
Le système a deux niveaux de prompt :


prompts/base/dev.md          ← instructions générales
prompts/stacks/nextjs-clerk-prisma/rules_dev.md  ← règles stack spécifiques
C'est une bonne séparation en principe. Mais à l'exécution, les deux sont concaténés et injectés comme system prompt. Le LLM reçoit donc potentiellement :

dev.md (base)
rules_dev.md (stack)
prompt_rules.* depuis le JSON (extraction_rules, auth_rules, ui_rules, orm_rules, security_rules, test_rules)
27 standards RAG mandatory
L'ordering_block, le requirements_block, le spec_degraded_block...
Le system prompt du dev agent est assemblé dynamiquement depuis 6 sources différentes. Le LLM reçoit un mur de texte dont personne ne peut prévoir exactement le contenu à chaque run.

Problème des prompts actuels :

dev.md est concis et focalisé — 36 lignes montrées, bonnes règles concrètes avec exemples de code. C'est la bonne direction.

rules_dev.md suit le même principe — règles numérotées avec exemples copy-paste. Bien.

Mais prompt_rules dans le JSON duplique ces règles en prose moins précise :


"auth_rules": ["Auth stack: Clerk uniquement; interdits: bcrypt..."]
La même règle existe en version claire avec exemples dans rules_dev.md ET en version prose approximative dans prompt_rules.auth_rules. Laquelle le LLM suit-il ?

4. Le brief_parser — Bien mais avec un bug silencieux
Le brief_parser est le composant le plus solide du projet. Extraction déterministe, résultat fiable.

Mais : le bug vu dans les logs — /POST → app/PO — vient du parser qui traite "GET/POST /api/products" comme une page avec chemin "/POST". Ce bug pollue le normalized_brief et donc le plan du planner. C'est un bug discret dans le regex du parser qui a des conséquences en cascade dans toute la pipeline.

5. Le dev_reflection.py — Invisible mais présent
Ce module génère un ProgressSummary et un build_iteration_brief injectés dans le contexte du dev agent à chaque itération. C'est un résumé de l'état courant (fichiers écrits, fichiers manquants, requirements couverts).

Bonne idée en principe — orienter le LLM vers ce qui reste à faire. Mais injecter un résumé à chaque itération augmente la taille du contexte à chaque tour. Au bout de 10 itérations, le dev agent reçoit un historique lourd.

6. Les Contrats JSON — Input/Output validation
Chaque activity a un contrat JSON validé à l'entrée et à la sortie. C'est une bonne pratique pour détecter les bugs d'intégration. Rien à simplifier ici — c'est de l'infrastructure saine.

7. Le QA Agent et le Test Coverage Agent
Ces agents tournent après le dev agent si le build réussit. Dans la situation actuelle (0 builds réussis), ils ne sont jamais atteints — donc leur complexité n'est pas un problème immédiat. À revisiter quand la factory produit des builds stables.

8. Le Learner Agent — Shadow mode
Le learner observe les runs et extrait des anti-patterns depuis last_build_error via _normalize_build_error(). Il envoie des suggestions à Qdrant (Zone 14) si validées via approve_suggestion.py.

Problème de principe : le learner apprend des erreurs pour enrichir les standards Qdrant. Mais si les standards Qdrant causent de la dérive (problème RAG discuté), le learner peut aggraver le problème en ajoutant des standards qui ont eux-mêmes causé des dérives. C'est une boucle de feedback qui peut diverger.

Tableau de Bord Final — Tout Composant
Composant	Verdict	Raison
templated_files (13 fichiers)	✅ Garder	Meilleure décision du projet
brief_parser	✅ Garder + corriger bug /POST	Fondation déterministe solide
requirements[] depuis parser	✅ Garder	Source de vérité fiable
Temporal workflow	✅ Garder	Infrastructure robuste
blueprint.required_files	✅ Garder	Garde structurelle utile
packages / versions épinglées	✅ Garder	Critique pour reproductibilité
env_validation	✅ Garder	Déterministe, simple
active_blocker (RunStateComputer)	✅ Garder	Oriente le LLM efficacement
run_build() + tsc/eslint	✅ Garder	Feedback déterministe réel
Contrats JSON	✅ Garder	Bonne pratique d'intégration
rules_dev.md avec exemples code	✅ Garder + nettoyer	Format idéal pour guider un LLM
Pipeline 5 nœuds architect	❌ Simplifier → 2 nœuds	Trop de LLM en série
3 superviseurs LLM par fichier	❌ Supprimer	Compensent un prompt insuffisant
correction loop architect	❌ Supprimer	Inutile si pipeline upstream fiable
9 mandatory_rag_queries	❌ Déplacer vers system prompt statique	Standards invariants ≠ RAG dynamique
53 standards Qdrant avec entités concrètes	❌ Purger → ~15 standards techniques purs	Contamination domaine métier
import_remaps.source_fixes	❌ Supprimer	Sanitizer qui masque dérive prompt
content_guards (6)	❌ Supprimer	Doublonnent les règles prompt
Règles dupliquées (4 endroits)	❌ Unifier	Une règle = un endroit
spec_validation.required_sections	❌ Assouplir	Rigidité sur le format, pas le contenu
supervision_routing	❌ Supprimer avec les superviseurs	Obsolète si superviseurs retirés
forbidden_auth_patterns + forbidden_imports	❌ Fusionner	Même règle, deux listes
learner agent	⚠️ Suspendre	Peut aggraver dérive si standards Qdrant problématiques
dev_reflection.py ProgressSummary	⚠️ Évaluer	Utile mais alourdit le contexte
FileSupervisionLoop	❌ Supprimer avec superviseurs	Infrastructure liée aux superviseurs
PreBuildValidator content_guards	❌ Simplifier → blueprint only	Garde utile, content checks inutiles
Le Principe Directeur de la Cure
Le problème central n'est pas que le code est mal écrit — c'est que chaque composant a été ajouté pour compenser le précédent. Le résultat est un système où la complexité est là pour gérer la complexité.

La cure consiste à inverser ça : simplifier l'input du LLM jusqu'à ce qu'il n'ait pas besoin d'être corrigé, plutôt que complexifier les corrections jusqu'à ce qu'elles couvrent toutes les dérives.

Un LLM bien guidé avec un input clair et minimal produit un output fiable. Un LLM mal guidé avec 6 couches de correction produit un output imprévisible malgré les corrections.


