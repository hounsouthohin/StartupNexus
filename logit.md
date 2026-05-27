






La Vision : Ce que la Startup Devrait Devenir
L'Inversion Fondamentale
Toute l'expérience accumulée pointe vers une vérité contre-intuitive : le LLM ne doit pas écrire du code — il doit enrichir une spécification que des générateurs transforment en code.

L'approche initiale était :


Brief → LLM écrit du code → on ajoute des règles pour corriger le LLM
La bonne approche, révélée par l'expérience :


Brief → LLM produit une spec riche → générateurs produisent du code depuis la spec
Ce n'est pas une nuance. C'est un changement d'identité complet de la factory.

Architecture Cible en 4 Couches
Couche 1 — Foundation Déterministe Pure

Input : schéma Prisma DSL + structure de pages basique
Output : app CRUD fonctionnelle à 70%

Aucun LLM. Purement dérivé du schéma. Pour chaque modèle, les générateurs produisent automatiquement les types, services, actions, pages list/create/edit/detail, forms, navigation, middleware, tests de structure. C'est le cœur stable — il doit être robuste, testé, et extensible.

Analogie : ce que create-t3-app fait pour le scaffold, mais poussé jusqu'à une app CRUD complète et fonctionnelle.

Couche 2 — Enrichissement Sémantique par LLM

Input : brief naturel + schéma
Output : spécification enrichie (JSON compact, validatable)

Le LLM a un seul rôle ici : lire le brief, comprendre le domaine métier, et annoter la spec avec ce que les générateurs ne peuvent pas deviner depuis le schéma seul :

Types sémantiques des champs ("textarea", "currency", "status", "priority")
Queries métier nécessaires (getByStatus, assignTo, countByCategory)
Flows utilisateur non-standards (dashboard avec agrégations, vue calendrier, etc.)
Règles de visibilité (auth_required: false pour les pages publiques)
Le LLM produit du JSON structuré, pas du TypeScript. Annoter une spec est infiniment plus fiable pour un LLM que d'écrire du code. Les erreurs sont détectables, corrigeables, validables par schema JSON.

Couche 3 — Génération Spec-Driven

Input : spec enrichie de la Couche 2
Output : app à 90-95%

Les générateurs utilisent maintenant les annotations sémantiques pour prendre des décisions intelligentes : le bon type d'input pour chaque champ, les bonnes queries dans les services, les bons layouts pour les pages spéciales. Pas d'heuristiques fragiles — des décisions explicites depuis la spec.

Couche 4 — Gap Filling LLM (minimal)

Input : liste des fichiers non-générables déterministiquement + contexte ciblé
Output : les 5-10% restants (logique métier très spécifique, dashboards complexes)

Le LLM intervient avec ~700 tokens de contexte — uniquement ce dont il a besoin pour ce fichier précis. Pas de 116 standards Qdrant. Pas de rules_dev.md. Juste les types adjacents, les services disponibles, et le contrat du fichier à produire. Un seul essai. Pas de boucle de correction.

Le Rôle Nouveau du LLM
Dans cette vision, le LLM a trois rôles distincts et bornés :

Rôle	Input	Output	Fiabilité
Brief Writer	Texte naturel	Spec JSON structurée	Haute — JSON validatable
Semantic Annotator	Spec basique + brief	Spec enrichie (annotations)	Haute — domaine restreint
Gap Filler	Contrat fichier + contexte ciblé	1 fichier TypeScript	Moyenne — dernier recours
Ce que le LLM ne fait jamais dans ce modèle : générer des fichiers structuraux (types, services, forms, actions, navigation, middleware). Ces fichiers suivent des patterns que le code Python maîtrise mieux qu'un LLM.

Infrastructure des Générateurs à Reconstruire
Pour que cette vision fonctionne, les générateurs doivent être refondus :

Moteur de templates (Jinja2 ou équivalent) plutôt que concaténation de strings Python. Un template edit_client.tsx.j2 est lisible, testable, modifiable sans risque de régression syntaxique.

Modèle sémantique de spec : une dataclass Python riche qui représente un champ non pas comme {name: "description", type: "String"} mais comme {name: "description", semantic_type: "textarea", display_label: "Description", required: true}. La Couche 2 LLM remplit ce modèle. Les générateurs le consomment.

Modules de features : au lieu de générateurs monolithiques, des modules indépendants par feature — module_crud, module_search, module_pagination, module_file_upload, module_status_workflow. Chaque module s'active si la spec déclare la feature. Chaque module est testable isolément.

Validation avant écriture : avant d'écrire un fichier sur disque, passer la string générée par un parser TypeScript léger (ts-morph en mode parse-only) pour détecter les erreurs de syntaxe. Une erreur de générateur se voit immédiatement, sans attendre le build complet.

La Progression par Niveaux

Level A (maintenant) : Brief structuré → CRUD app basique
                       Déterminisme ~97%, LLM ~3%
                       Problème : générateurs fragiles

Level B (prochain)   : Brief naturel → Spec enrichie → CRUD app + queries métier
                       Déterminisme ~90%, LLM ~10% (annotation + gap fill)
                       Clé : LLM produit des specs, pas du code

Level C (futur)      : Brief naturel → App complexe (dashboard, search, workflows)
                       Modules features activables depuis spec
                       Déterminisme ~80%, LLM ~20% (logique spécifique)

Level D (horizon)    : Multi-stack
                       Même pipeline d'annotation spec, générateurs différents
                       La spec enrichie est stack-agnostique
Pourquoi Ce Chemin Fonctionne
Scalabilité : générer 100 apps différentes sur Next.js/Clerk/Prisma devient trivial — c'est le même pipeline, des specs différentes. Les générateurs s'améliorent une fois, toutes les apps en bénéficient.

Fiabilité : le code déterministe est testé une fois et stable. Les bugs LLM sont confinés aux 5-10% de gap filling, pas distribués sur 100% des fichiers.

Auditabilité : le chemin brief → spec → code est traçable. On peut inspecter la spec enrichie, voir ce que le LLM a annoté, comprendre pourquoi le générateur a produit tel code.

Évolutivité : ajouter le support d'un nouveau pattern (file upload, real-time, multi-tenant) = écrire un module generator + ajouter l'annotation correspondante dans le Semantic Annotator LLM. Pas besoin de réécrire tout l'écosystème.

L'IA à sa juste place : le LLM excelle à comprendre le langage naturel et à structurer de l'information. Il est médiocre pour produire du code syntaxiquement parfait à chaque fois. Ce modèle joue les forces du LLM (compréhension sémantique → spec) et les forces du code déterministe (fiabilité syntaxique → fichiers).

En Une Phrase
La Software Agent Factory doit devenir un compilateur de briefs : le LLM traduit l'intention humaine en spécification formelle enrichie, et des générateurs robustes compilent cette spécification en application fonctionnelle — avec le LLM comme dernier recours ciblé pour ce que la compilation ne peut pas couvrir.