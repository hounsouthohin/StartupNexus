# 🚀 ROADMAP AGILE 2026 — SOFTWARE AGENT FACTORY
## Version 2.0 — Flexibilité · Modularité · Apprentissage
## Date : 23 Février 2026

---

## 🎯 VISION (inchangée)

Usine logicielle 100% autonome et auto-apprenante transformant 
une commande humaine en application full-stack déployée, testée, 
sécurisée et constamment améliorée, sans intervention humaine.

## 🏛️ PRINCIPES ARCHITECTURAUX v2.0

Trois principes non négociables qui guident chaque décision :

PRINCIPE 1 — Le code exécute, la configuration décide
  Toute règle stack-spécifique vit dans config/stacks/*.json
  Le code Python est un exécuteur générique
  Ajouter une stack = créer un fichier JSON, zéro Python modifié

PRINCIPE 2 — Standards prescriptifs, pas descriptifs
  Chaque standard dit : INTERDIT X, OBLIGATOIRE Y, PRÉFÉRÉ Z
  Avec DETECTION_REGEX, EXEMPLE_INVALIDE, ERREUR_ATTENDUE
  Un standard sans règle négative est incomplet

PRINCIPE 3 — La boucle d'apprentissage doit être fermée
  RAG → Agent → Erreur → Learner → RAG
  Chaque maillon doit être implémenté avant de passer au suivant
  Les patches silencieux masquent l'apprentissage → les rendre visibles

---

## PHASE 0 + SPRINT 0.5 + SPRINT 1 ✅ TERMINÉS (inchangés)

---

## SPRINT 2 — Clôture Officielle

STATUT : EN COURS — build_success=false
DATE CLÔTURE RÉELLE : dès que build_success=true obtenu

SEULS 2 FIXES RESTANTS :

Fix 1 — shared_tools.py CLERK_TEST_MOCK_FIXES :
  Ajouter : "@clerk/nextjs/api": "@clerk/nextjs/server"

Fix 2 — shared_tools.py JEST_REQUIRED_DEV_DEPS :
  Ajouter : "node-mocks-http": "^1.14.0"

Fix 3 — 3 standards prescriptifs Qdrant :
  INTERDIT pages/ quand app/ existe
  INTERDIT import @clerk/nextjs/api
  OBLIGATOIRE node-mocks-http pour tests API Routes

SIGNAL DE CLÔTURE : build_success=true sur 1 run

ACQUIS RÉELS SPRINT 2 :
  ✅ Pipeline end-to-end Architect→Dev→QA→GitHub→Learner
  ✅ 25 fichiers générés par run
  ✅ RAG actif avec k=5, 64 standards
  ✅ Sanitizers : Clerk fix, VERSION_PINS, middleware V4→V5
  ✅ Séparation workflow_status / build_status
  ✅ Fix App Router/Pages Router (_remove_pages_router_conflicts)
  ✅ Learner shadow : 9 events/run, baseline 13.8
  ✅ Stack-as-Config : dev_packages injecté depuis JSON (plus hardcodé)
  ✅ Stack-as-Config : spec_validation branché dans architect.py
  ✅ Stack-as-Config : templates system éliminé (shared_tools.py)
  ✅ Fix EJSONPARSE : _fix_json_escaping() dans shared_tools.py
  ✅ Fix Phase 1→2 : transition dynamique liste les required_files manquants
  ✅ Fix Clerk v6 : source_fixes + Qdrant standards corrigés (v5→v6)
  ✅ Audit "Version-Semantic Drift" : populate_qdrant.py corrigé (4 standards faux)
  ✅ clerk_compliant=true + semantic_violations=[] atteints (Run 4)
  BLOQUEUR ACTUEL : casing conflit test files (Layout.test.tsx vs layout.test.tsx)

---

## SPRINT 3 — Stabilisation + Fondations Modularité
## Deadline : 7 Mars 2026 (réaliste, pas 24 Fév)

OBJECTIF : Poser les fondations qui rendront chaque sprint suivant
plus facile à construire. Pas de nouvelles features sur base instable.

### Phase A — Sécurité + Nettoyage (J1-J2)

1. SÉCURITÉ CRITIQUE :
   - Rotation OPENAI_API_KEY et GITHUB_TOKEN
   - .env ajouté au .gitignore
   - Audit historique git (suppression clés exposées)
   - .env.example créé (template sans valeurs)

2. NETTOYAGE PROJET :
   - Supprimer variables .env inutilisées 
     (TEMPORAL_VERSION, ELASTICSEARCH_VERSION, OLLAMA_MODEL)
   - Archiver logs/metrics anciens (garder 3 derniers)
   - Unifier _log_patch() — 1 helper central au lieu de 9 inline
   - Commenter config/agents_config.yaml comme "documentaire uniquement"
   - Supprimer fonctions doublons shared_tools.py

3. CENTRALISER PROMPT LOADER :
   - architect.py, qa.py, test_coverage.py 
     → tous via utils/prompt_loader.py
   - Zéro loader custom par agent

### Phase A-bis — Fix Bloqueur Casing (J1, priorité immédiate)

PROBLÈME : Sur Linux (container Docker, filesystem case-sensitive), deux fichiers
de test avec noms différant uniquement par la casse coexistent :
  tests/app/Layout.test.tsx (dev agent, suit le nom du composant)
  tests/app/layout.test.tsx (qa agent, convention minuscule)
TypeScript avec forceConsistentCasingInFileNames=true refuse de compiler.
ERREUR : "File name differs from already included file name only in casing"

FIX 1 — write_file() dans shared_tools.py :
  Normaliser les chemins de fichiers de test en minuscules avant écriture.
  Empêche mécaniquement la coexistence de fichiers en conflit de casse.

FIX 2 — tsconfig.json généré :
  Exclure tests/ du build TypeScript next.
  Les tests sont compilés par Jest séparément, pas par next build.
  Ajouter "tests/**" dans exclude du tsconfig.

### Phase B — Stack-as-Config (J3-J5) ← NOUVEAU CONCEPT CLÉ

PRINCIPE : Extraire toutes les règles stack-spécifiques du code Python
vers un fichier de configuration déclaratif.

CRÉER config/stacks/nextjs-clerk-prisma.json :

{
  "id": "nextjs-clerk-prisma",
  "version": "1.0",
  "display_name": "Next.js 14 + Clerk v5 + Prisma 7",
  "status": "stable",

  "packages": {
    "next": "14.2.25",
    "react": "^18.2.0",
    "@clerk/nextjs": "^6.0.0",
    "@prisma/client": "^7.0.0"
  },

  "dev_packages": {
    "jest": "^29.0.0",
    "jest-environment-jsdom": "^29.0.0",
    "@testing-library/react": "^14.0.0",
    "@testing-library/jest-dom": "^6.0.0",
    "node-mocks-http": "^1.14.0",
    "ts-jest": "29.1.2",
    "@babel/runtime": "^7.0.0"
  },

  "forbidden_paths": ["pages/"],
  "forbidden_imports": [
    "@clerk/nextjs/api",
    "next-auth",
    "@clerk/clerk-sdk"
  ],
  "forbidden_packages": ["shadcn/ui", "@clerk/clerk-sdk", "next-auth"],

  "import_remaps": {
    "@clerk/clerk-sdk": "@clerk/nextjs",
    "@clerk/nextjs/middleware": "@clerk/nextjs/server",
    "@clerk/nextjs/api": "@clerk/nextjs/server"
  },

  "blueprint": {
    "required_files": [
      "app/layout.tsx",
      "app/page.tsx",
      "middleware.ts",
      "schema.prisma",
      "package.json",
      "tsconfig.json",
      "jest.config.js",
      "jest.setup.js"
    ],
    "optional_files": [
      "app/api/*/route.ts",
      "app/components/*.tsx",
      "app/utils/*.ts"
    ]
  },

  "commands": {
    "install": "npm install --legacy-peer-deps",
    "build": "npm run build",
    "test": "npx jest --coverage",
    "migrate": "npx prisma migrate dev"
  },

  "qdrant_filter": {
    "must": [
      {"key": "metadata.stack", "match": {"any": ["nextjs-clerk-prisma", "global"]}}
    ]
  },

  "prompt_folder": "prompts/stacks/nextjs-clerk-prisma/",

  "compatibility_matrix": [
    {"next": "14.2.25", "clerk": "6.x", "prisma": "7.x", "status": "validated"},
    {"next": "15.x", "clerk": "6.x", "prisma": "7.x", "status": "experimental"}
  ],

  "sanitizers": [
  "remove_pages_conflicts",
  "clerk_middleware_v5",
  "remove_problematic_babel"
],

"build_hooks": {
  "pre_build": ["remove_pages_conflicts"],
  "pre_test": ["inject_jest_config", "inject_clerk_mocks"]
}
}
CONFIG-RUNTIME DRIFT — 3 champs JSON confirmés non-consommés par le runtime :
  (identifiés par audit grep sur agents/ — zéro match)

  1. qdrant_filter : déclaré dans JSON, ignoré par rag_search()
     → rag_search retourne des standards de toutes les stacks (noise shadcn, etc.)
     → FIX Sprint 3 : brancher qdrant_filter dans rag_search() via stack_cfg
     → IMPACT : élimination du noise cross-stack dans les résultats RAG

  2. commands : déclaré dans JSON, run_build() hardcode "npm install" + "npm run build"
     → FIX Sprint 3 : run_build() lit commands.install et commands.build depuis stack_cfg
     → IMPACT : finalise Stack-as-Config pour la couche d'exécution

  3. test_import_rules : déclaré dans JSON, non branché dans les agents
     → FIX Sprint 4 (moins critique) : brancher dans test_coverage.py

VALIDATION CONFIG — 2 NIVEAUX (distinction critique) :

  NIVEAU 1 — Validation structurelle (existante) :
    validate_contracts.py → vérifie que le JSON est bien formé selon le schéma
    Status : ✅ opérationnel
    Limite : un JSON peut être "valide au schéma" mais ses champs ignorés à l'exécution

  NIVEAU 2 — Validation comportementale (à créer Sprint 3) :
    validate_config_consumption.py → vérifie que chaque champ déclaré dans
    config/stacks/*.json est effectivement LU par le code runtime.

    Approche : grep automatique du code agents/ + shared_tools.py
    pour chaque clé déclarée dans le JSON de stack.

    Exemple de règles :
      "qdrant_filter" déclaré → chercher "qdrant_filter" dans rag_search()
      "commands.build" déclaré → chercher "commands" dans run_build()
      "dev_packages" déclaré → chercher "dev_packages" dans dev.py ou shared_tools.py

    OUTPUT : rapport {champ: "declared|consumed|DRIFT"}
    Un champ en DRIFT = Config-Runtime Drift confirmé → action requise.

    Différence avec validate_contracts.py :
      validate_contracts = "le JSON est-il bien écrit ?"
      validate_config_consumption = "le JSON est-il bien utilisé ?"

    À CRÉER : scripts/validate_config_consumption.py
    SIGNAL : tous les champs actifs marqués "consumed" avant clôture Sprint 3

ATTENTION — Procédure Qdrant (à respecter après chaque mise à jour des standards) :
  reset_qdrant.py utilise des UUIDs déterministes basés sur MD5(texte).
  Si le texte d'un standard change, l'ancien vecteur (faux) reste dans Qdrant.
  Les deux coexistent → le RAG peut retourner l'ancien ET le nouveau.
  ORDRE OBLIGATOIRE après modification de populate_qdrant.py :
    1. python scripts/reset_qdrant.py       (purge totale)
    2. python scripts/populate_qdrant.py    (réinjection corrigée)
    3. python scripts/create_sprint2_prescriptive_standards.py (standards prescriptifs)

CONCEPT — SanitizerRegistry (conception Sprint 3, implémentation Sprint 6-7)
Chaque sanitizer = une classe Python enregistrée par nom.
Le JSON stack config liste les sanitizers à appliquer par nom.
Ajouter un sanitizer pour une nouvelle stack = 1 fichier Python + 1 ligne JSON.
Zéro sanitizer existant modifié.
C'est ce qui rend la promesse "<5% Python Sprint 8" réaliste.

IMPACT IMMÉDIAT :
  - shared_tools.py lit ce fichier au lieu d'avoir des constantes
  - VERSION_PINS, CLERK_PACKAGE_FIXES, JEST_REQUIRED_DEV_DEPS
    → supprimés du code Python, lus depuis le JSON
  - Rigidité : 8.8/10 → ~5/10 estimé

  FONDATION CRITIQUE — Run ID propagé (2h de travail, impact Sprint 4-5)

run_id = str(uuid4()) généré au démarrage de chaque workflow
Propagé obligatoirement à :
  - tous les appels _write_learner_event(run_id=run_id, ...)
  - _append_rag_usage_event(run_id=run_id, doc_ids=[IDs Qdrant réels], scores=[...])
  - .factory-meta.json généré dans chaque projet

IMPORTANT : rag_usage.jsonl doit stocker les IDs Qdrant réels
des documents retournés, pas des snippets de 180 chars.
Sans ça, Mode Replay Sprint 5 et anti-patterns Sprint 4 sont impossibles.

RISQUE IDENTIFIÉ — Prompt Concat Scalability Risk :
  Aujourd'hui : base_prompt + rules_dev.md (concaténation simple)
  Fonctionne bien tant que rules_dev.md reste court (<20 règles).
  Quand les règles grossissent :
    - conflits/incohérences entre règles
    - dilution des priorités (LLM ne sait plus quoi appliquer en premier)
    - surcharge de contexte (moins de place pour la tâche réelle)
  Symptôme observé : Run 3 avait les bonnes règles dans le prompt mais
  le RAG renvoyait auth().protect() comme "validated" → le RAG gagnait.
  DÉCISION ARCHITECTURE Sprint 3+ :
    RAG = source principale de guidance (exemples concrets, patterns validés)
    rules_dev.md = guardrails courts (<15 règles) — ne pas y mettre de code
    Un standard Qdrant bien rédigé > 3 lignes dans rules_dev.md

### Phase C — Standards Prescriptifs + Blueprint (J5-J7)

1. STANDARDS PRESCRIPTIFS — Reformater les standards critiques
   existants avec le nouveau template :

   Template obligatoire pour tout nouveau standard :
   
   ACTION: INTERDIT | OBLIGATOIRE | PRÉFÉRÉ | DÉPRÉCIÉ
   STACK: nextjs-clerk-prisma | global
   TECHNOLOGIE: <package ou pattern exact>
   RAISON: <impact concret si violé>
   DETECTION_REGEX: <pattern de détection>
   ALTERNATIVE: <quoi utiliser à la place>
   EXEMPLE_INVALIDE: <code qui échoue>
   EXEMPLE_VALIDE: <code correct>
   ERREUR_ATTENDUE: <message d'erreur exact>
   STATUS: active
   VERSION: 1.0

NOUVEAU — VERSION-SEMANTIC DRIFT (classe de problème identifiée Sprint 2) :
  Définition : un package est épinglé à une version dans stack JSON, mais les
  standards Qdrant référencent des patterns de l'ancienne version API.
  Résultat : le RAG enseigne activement le MAUVAIS code au LLM.
  Exemple concret : stack dit @clerk/nextjs ^6.0.0, Qdrant avait auth().protect()
  comme "validated" (pattern v5) → LLM copiait l'exemple faux du RAG.
  RÈGLE Sprint 3 : après chaque upgrade de version dans stack JSON,
  auditer et corriger TOUS les standards Qdrant référençant cette technologie.
  AUDIT = grep sur populate_qdrant.py + create_sprint2 pour version mismatch.

2. TAGGER LES 64 STANDARDS EXISTANTS :
   - Ajouter metadata.stack = "nextjs-clerk-prisma" ou "global"
   - Ajouter metadata.status = "active"
   - Ajouter metadata.version = "1.0"
   - Filtrer rag_search par stack_id dès maintenant

3. BLUEPRINT VALIDATOR :
   Avant run_build(), vérifier que tous les required_files
   du blueprint sont présents. Si un fichier manque :
   log WARNING + continuer (pas bloquant Sprint 3, bloquant Sprint 4)

4. STACK_ID COMME PARAMÈTRE D'ENTRÉE :
   Le workflow reçoit stack_id = "nextjs-clerk-prisma" (hardcodé pour
   l'instant, dynamique Sprint 4)
   Chaque activity reçoit et transmet le stack_profile chargé

### Phase D — LearnerActivity (J7-J9) ← FONDATION CRITIQUE

CRÉER agents/learner.py avec LearnerActivity Temporal :

Structure minimale Sprint 3 (shadow mode) :

class LearnerActivity:
  async def analyze_run(self, run_id, events, build_success):
    
    # 1. Compter les patches appliqués
    patches = [e for e in events if e.type == "tool_patch_applied"]
    
    # 2. Identifier les patterns récurrents
    # (patch du même type sur 3+ runs consécutifs = candidat standard)
    patterns = self._detect_recurring_patterns(patches)
    
    # 3. Générer StandardSuggestion structurée (pas juste un log)
    suggestions = []
    for pattern in patterns:
      if pattern.frequency >= 3:
        suggestions.append(StandardSuggestion(
          action="INTERDIT" if pattern.is_error else "OBLIGATOIRE",
          technology=pattern.target,
          evidence=pattern.run_ids,
          confidence=pattern.frequency / 10,
          requires_human_approval=True
        ))
    
    # 4. Écrire dans learner_suggestions.json (pas Qdrant direct)
    self._write_suggestions(suggestions)
    
    return {"patterns": len(patterns), "suggestions": len(suggestions)}

SIGNAL CLÔTURE SPRINT 3 :
  - build_success=true reproductible (2+ runs)
  - config/stacks/nextjs-clerk-prisma.json actif
  - VERSION_PINS supprimé du code Python
  - 64 standards taggés avec stack_id
  - LearnerActivity créée et loggant des StandardSuggestion
  - Secrets rotés + gitignore propre
  - Prompt loader centralisé (4/4 agents)

  ### Phase E — LearnerActivity connectée (J8-J10)

OBJECTIF : Connecter le Learner aux vraies données de patches.
Le learner.py existe mais génère des suggestions hardcodées
basées sur total_files < 8. Il ne lit jamais learner_shadow_log.json.

ACTIONS :
1. Modifier learner_agent() pour lire learner_shadow_log.json
   filtré par run_id (fondation posée en Phase B)

2. Remplacer les suggestions hardcodées par une analyse
   des patch_events avec classification :
   - trigger_context = "rag_retrieved"
     → le standard existe mais le LLM l'ignore
     → SUGGESTION : renforcer le prompt, pas le standard Qdrant
   - trigger_context = "tool_guardrail"
     → aucun standard ne couvrait ce cas
     → SUGGESTION : créer un standard prescriptif

3. Générer des StandardSuggestion structurées :
   {
     "patch_type": "import_remap",
     "trigger_context": "tool_guardrail",
     "evidence": [run_ids],
     "confidence": frequence / 10,
     "requires_human_approval": true
   }

4. Écrire dans learner_suggestions.json
   (pas Qdrant direct — validation humaine obligatoire)

SIGNAL : LearnerAgent produit des StandardSuggestion structurées,
         pas des logs bruts

---

## SPRINT 4 — Gate Décisionnel + Modularité Avancée
## Deadline : Mars 2026

OBJECTIF : Valider empiriquement l'architecture + fermer la boucle
d'apprentissage + préparer multi-stack

### Nouveautés v2.0 (absentes de v1.5)

1. ANTI-PATTERNS AUTOMATIQUES :
   Quand un run échoue avec une erreur récurrente, le LearnerAgent
   crée automatiquement un anti-pattern dans Qdrant :
   
   {
     "type": "anti_pattern",
     "stack": "nextjs-clerk-prisma",
     "error_signature": "Conflicting app and page file",
     "cause": "pages/ coexiste avec app/",
     "fix": "Supprimer pages/ quand app/ existe",
     "observed_in_runs": 7,
     "status": "active"
   }
   
   Ces anti-patterns sont récupérés en priorité haute dans rag_search
   — l'agent apprend des erreurs passées avant de générer.

2. CONTRACT DE SORTIE INTER-AGENTS :
   Chaque transition agent→agent valide un JSON Schema strict.
   Si l'Architect ne spécifie pas router_type="app", le système
   refuse de passer à DevAgent (et non le DevAgent qui devine).
   
   Architect Output Contract v2 (ajouts) :
   {
     "router_type": "app",        // OBLIGATOIRE
     "stack_id": "nextjs-...",    // OBLIGATOIRE  
     "forbidden_paths": [...],    // transmis depuis stack config
     "required_files": [...]      // blueprint transmis
   }

3. BLUEPRINT VALIDATOR BLOQUANT :
   Passer de WARNING (Sprint 3) à BLOQUANT :
   Si required_files manquants → DevAgent itère jusqu'à complétion
   avant de lancer run_build

4. GATE DÉCISIONNEL (inchangé de v1.5) :
   Review LearnerAgent suggestions (15-20 cumulées)
   Validation humaine >70% → activation mode actif Sprint 5
   Baseline mobile 3 projets activée

5. QDRANT GOVERNANCE v1 :
   Standards avec status: active | deprecated | archived
   Quand un standard est superseded : ancien passe à deprecated
   Qdrant ne retourne que status=active
   
   {
     "id": "clerk-auth-v5",
     "version": "2.0",
     "supersedes": "clerk-auth-v4",
     "status": "active",
     "valid_from": "2026-02-23"
   }

SIGNAL CLÔTURE SPRINT 4 :
  - 3 projets production avec build_success=true
  - Gate décisionnel documenté
  - Anti-patterns créés automatiquement
  - Contracts inter-agents v2 validés
  - LearnerAgent : >15 suggestions générées
  - Suggestions validées >70% → Sprint 5 activé

---

## SPRINT 5 — LearnerAgent Actif + Maintenance Standards
## Deadline : Avril 2026 (inchangé)

OBJECTIF : Fermer complètement la boucle RAG→Agent→Erreur→Learner→RAG

NOUVEAUTÉS v2.0 :

1. MODE REPLAY :
   Si run N échoue et run N-1 réussissait, le système compare :
   - Fichiers générés (diff)
   - Standards récupérés par RAG (quels IDs)
   - Décisions LLM (patches appliqués)
   Identifie exactement où la divergence s'est produite.
   Outil de debugging radical pour identifier les standards insuffisants.

2. COMPATIBILITY MATRIX DYNAMIQUE :
   Au lieu d'épingler next@14.2.25 dans le code,
   le StandardsMaintenanceAgent maintient la matrice :
   
   {next: "14.2.25", clerk: "6.x", prisma: "7.x"} → VALIDATED
   {next: "15.x", clerk: "6.x", prisma: "7.x"} → EXPERIMENTAL
   
   ```
CRITÈRE DE PROMOTION (évite que la matrice reste déclarative) :
  2 runs build_success=true avec une combinaison → promue "validated"
  1 run build_success=false → reste "experimental"
  3 runs build_success=false → marquée "unstable"

Ce critère est automatisable par le StandardsMaintenanceAgent.
   
   Le DevAgent récupère la combinaison VALIDATED avant package.json.
   Quand Clerk sort v7 → on ajoute une ligne, zéro Python modifié.

3. WEB SEARCH → STANDARD (inchangé de v1.5, mais intégré à la stack)

SIGNAL CLÔTURE SPRINT 5 :
  - Boucle RAG→Learner→RAG fermée et prouvée (≥1 upsert validé)
  - Mode Replay opérationnel
  - Compatibility matrix dans Qdrant (remplace VERSION_PINS total)
  - Web search actif avec allowlist sources

---

## SPRINT 6 — Frontend Pro + Dashboard Gouvernance + SanitizerRegistry
## Deadline : Avril 2026 (inchangé)

AJOUT v2.0 — SANITIZERREGISTRY (migration dette technique pre-build hooks) :

  CONTEXTE DETTE :
  Les fonctions pre-build suivantes dans shared_tools.py violent PRINCIPE 1
  (logique stack-specific codée en Python, pas en JSON) :
    - _remove_pages_tests_router_conflicts()  [App Router / Pages Router]
    - _ensure_nextconfig_eslint_ignore()      [eslint config]
    - _ensure_layout_dynamic()               [Clerk publishableKey prerender]
    - _fix_nextconfig_security_headers()     [Next.js headers() format]
    - _ensure_layout_html_body()             [App Router <html>/<body>]

  SOLUTION SanitizerRegistry :
  Chaque correctif devient un Sanitizer nommé, déclaré dans config/stacks/*.json :
    sanitizers: [
      "NextjsRemovePagesConflicts",
      "NextjsEslintIgnore",
      "NextjsForceLayoutDynamic",
      "NextjsFixHeadersFormat",
      "NextjsEnsureHtmlBody"
    ]
  Python itère sur la liste et dispatche → zéro logique stack-specific en Python.
  Ajouter un sanitizer = 1 classe Python générique + déclaration JSON.

  ACCEPTATION DETTE SPRINT 2 :
  Appliqué en option A (pragmatique) : fonctionnel maintenant, migré Sprint 6.
  Documenté changelog #30, #31, #32.

Inchangé de v1.5 — mais avec ajout :

AJOUT v2.0 — DASHBOARD STACK MANAGER :
  En plus du dashboard standards, interface pour gérer les stacks :
  - Voir config/stacks/*.json actives
  - Modifier une stack (packages, forbidden_paths, blueprint)
  - Créer une nouvelle stack (formulaire → génère le JSON)
  - Voir les standards associés à chaque stack
  
  C'est la préparation visuelle au multi-stack Sprint 8.

---

## SPRINT 7 — Meta-Learning + Versioning
## Deadline : Mai 2026 (inchangé)

Inchangé de v1.5 avec un ajout :

AJOUT v2.0 — STACK VERSIONING :
  Une stack peut avoir des versions :
  nextjs-clerk-prisma@1.0 → next@14.2.25 (stable)
  nextjs-clerk-prisma@2.0 → next@15.x (quand stable)
  
  Un projet généré est lié à la version de stack utilisée.
  Rollback possible si la nouvelle version génère des régressions.

---

## SPRINT 8 — Multi-Stack Full
## Deadline : Mai 2026

CHANGEMENT MAJEUR v2.0 vs v1.5 :

v1.5 prévoyait "<40% modification code agents" pour le POC multi-stack.
Avec Stack-as-Config en place depuis Sprint 3 :
Effort estimé : "<5% modification code Python"

La seule chose à créer pour Vue.js + FastAPI :
1. config/stacks/vue-fastapi-sqlalchemy.json
2. Standards Qdrant taggés stack=vue-fastapi-sqlalchemy
3. Prompts dans prompts/stacks/vue-fastapi-sqlalchemy/

Zéro modification agents/, workflows/, shared_tools.py

CRITÈRE SUCCÈS RÉVISÉ :
  - 1 projet Vue.js/FastAPI généré avec build_success=true
  - <5% code Python modifié (vs <40% en v1.5)
  - Preuve que Stack-as-Config fonctionne

---

## SPRINT 9 — Production Ready
## Deadline : 15 Mai 2026 (inchangé)

Inchangé de v1.5.

---

## 🎯 JALONS RÉVISÉS v2.0

| Date cible | Livrable | Signal mesurable |
|------------|----------|-----------------|
| Dès possible | Sprint 2 clôturé | build_success=true sur 1 run |
| 7 Mars 2026 | Sprint 3 terminé | Stack-as-Config actif + Run ID propagé +
                                  LearnerActivity connectée + Standards prescriptifs |
| Fin Mars 2026 | Sprint 4 terminé | Gate décisionnel + anti-patterns auto |
| Fin Avril 2026 | Sprints 5-6 | Boucle fermée + web search + dashboard |
| Mi-Mai 2026 | Sprints 7-8 | Meta-learning + multi-stack <5% Python |
| 15 Mai 2026 | Sprint 9 | Démo 50 projets autonomes |

---

## 📊 CHANGEMENTS v1.5 → v2.0

| # | Type | Description |
|---|------|-------------|
```
#13 | Architecture | Stack-as-Config JSON + SanitizerRegistry concept | Sprint 3
#14 | Standards    | Format prescriptif obligatoire (INTERDIT/OBLIGATOIRE/PRÉFÉRÉ) | Sprint 3
#15 | Fondation    | Run ID propagé partout (base Mode Replay + anti-patterns) | Sprint 3
#16 | Apprentissage| trigger_context dans patch events (prompt vs RAG insuffisant) | Sprint 3
#17 | Apprentissage| Anti-patterns automatiques dans Qdrant | Sprint 4
#18 | Contrats     | Inter-agent contracts v2 (router_type, stack_id obligatoires) | Sprint 4
#19 | Debugging    | Mode Replay run N vs run N-1 | Sprint 5
#20 | Versions     | Critère promotion Compatibility Matrix (2 runs validés) | Sprint 5
#21 | Versions     | Stack versioning + .factory-meta.json par projet | Sprint 7
#22 | Multi-stack  | Effort <5% Python grâce SanitizerRegistry | Sprint 8
#23 | Dates        | Sprint 3 deadline 7 Mars (réaliste) | Immédiat
#24 | Bug class    | Version-Semantic Drift : Qdrant standards ≠ version stack config | Sprint 2 découvert, Sprint 3 procédure
#25 | Bug class    | Casing conflict test files : Layout.test.tsx vs layout.test.tsx Linux | Sprint 2 découvert, fix immédiat
#26 | Architecture | Config-Runtime Drift : qdrant_filter + commands non-consommés | Sprint 3 à brancher
#27 | Architecture | Prompt Concat Scalability : RAG=guidance, rules_dev.md=guardrails courts | Sprint 3 principe
#28 | Process      | Procédure Qdrant reset obligatoire avant re-populate (UUID déterministe) | Immédiat
#29 | Validation   | Niveau 2 config : validate_config_consumption.py (champ déclaré = champ consommé) | Sprint 3
#30 | Dette tech   | Pre-build hooks Python = violation PRINCIPE 1 (stack-specific en Python) → SanitizerRegistry Sprint 6-7 | Sprint 6-7
#31 | Bug class    | Next.js headers() format : LLM génère [{key,value}] au lieu de [{source, headers:[]}] → _fix_nextconfig_security_headers | Sprint 2 fix immédiat
#32 | Bug class    | App Router layout sans <html>/<body> : LLM génère React.FC classique → _ensure_layout_html_body | Sprint 2 fix immédiat