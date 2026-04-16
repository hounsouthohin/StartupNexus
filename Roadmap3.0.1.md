# 🚀 ROADMAP AGILE 2026 — SOFTWARE AGENT FACTORY
## Version 2.3 — Mise à jour 28 Mars 2026
## (v2.0 : 23 Fév 2026 — base · v2.1 : 03 Mars 2026 — Sprint 2 clôturé · v2.2 : 04 Mars 2026 — Sprint 3 + Audit fixes · v2.3 : 28 Mars 2026 — Refactorisation Architecture Simplifiée)

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

---

## REFACTORISATION ARCHITECTURE SIMPLIFIÉE ✅ COMPLÉTÉE
## Date : 27-28 Mars 2026 | Superviseur : Claude | Exécutants : Claude + Codex

OBJECTIF : Éliminer le LLM bloat, rendre le pipeline fiable et observable.
Contexte de départ : 3/3 runs en échec avec SPEC_DEGRADED_UNRECOVERABLE.

### Phase A — Pipeline Architect corrigé ✅
  A1 — spec_writer_node : requirements[] injectés en PREMIER dans input_text
       (avant : plan JSON en tête → LLM ignorait les requirements → SPEC_DEGRADED systématique)
  A2 — brief_parser : filtre /POST capturé comme page (bug regex "GET/POST /api/...")
  A3 — architect_activity : suppression de l'ApplicationError SPEC_DEGRADED_UNRECOVERABLE
       (la correction loop re-invoquait le même pipeline → cascade de failure garantie)
  Gate A ✅ : 3/3 runs atteignent le dev agent (plus de crash architect)

### Phase B — Stack JSON simplifié ✅ (exécuté par Codex)
  B1 — content_guards[] supprimé (~135 lignes) — doublons de rules_dev.md
  B2 — import_remaps{} supprimé (~28 lignes) — sanitizer anti-pattern
  B3 — supervision_routing{} supprimé (~10 lignes) — obsolète
  B4 — mandatory_rag_queries[] vidé + migré vers rules_dev.md (section "Concepts Stack Obligatoires")
  Fix complémentaire — schemas/stack_config.schema.json : import_remaps retiré du required[]
  Résultat : JSON 574 lignes → 392 lignes (réduction -32%)
  Gate B ✅ : aucune régression, import_remaps error disparue

### Phase C — Retrait LLM supervisors ✅
  C1 — supervision_manager.py : bloc Niveau 2 LLM supprimé (conformity/security/architecture)
       Supervision = déterministe uniquement (tsc + eslint)
  C2 — conformity_agent.py, security_agent.py, architecture_agent.py : marqués DÉPRÉCIÉS
       (conservés pour rétrocompatibilité imports, non appelés en production)
  Tests mis à jour : 2 tests LLM supervisor → @pytest.mark.skip
  Gate C ✅ : latence réduite, 2/3 runs à spec_coverage=1.0 + requirements_met=7/7

### Phase D — Purge Qdrant ✅ (exécuté par Codex)
  68 standards audités, 36 pollués détectés, 33 sanitisés
  Entités concrètes → placeholders [ENTITY], [MODEL_NAME], [entities]
  Modes ajoutés : --audit-only, --only-modified, --no-sanitize
  Validation : polluted_hits=0 sur 3 briefs tests (marketplace, habit-tracker, invoice-generator)
  Note : objectif ~15 standards non atteint (68 sanitisés) — pollution supprimée sans réduction de couverture
  Gate D ✅ : RAG propre sur tous les briefs testés

### Résultats observés post-refactorisation
  Avant : 3/3 runs SPEC_DEGRADED_UNRECOVERABLE (dev agent jamais atteint)
  Après : 3/3 runs COMPLETED, dev agent génère 13-29 fichiers par run
          2/3 runs : spec_coverage=1.0, requirements_met=7/7, is_useful_app=true
          Erreurs résiduelles : Prisma schema LLM (double @default, relation manquante)
          → problème qualité dev agent, hors scope refactorisation

### Ancien plan (plan.md) — archivé
  Phase 1 ✅ absorbée | Phase 2 partiellement absorbée | Phase 3 abandonnée
  Phase 4 ✅ absorbée (correction loop supprimée) | Phase 5 abandonnée
  Référence complète : PLAN_REFACTO_SIMPLIFIE.md

---

## PHASE 0 + SPRINT 0.5 + SPRINT 1 ✅ TERMINÉS (inchangés)

---

## SPRINT 2 — Clôture Officielle ✅ COMPLÉTÉ

STATUT : ✅ COMPLÉTÉ — 02 Mars 2026
DATE CLÔTURE RÉELLE : 02 Mars 2026 — Run 578623e6

SIGNAL DE CLÔTURE ATTEINT :
  ✅ build_success=true reproductible (5 runs consécutifs)
  ✅ tests_passed=true (premier atteint Run 578623e6 — 16:29)
  ✅ semantic_violations=[] reproductible
  ✅ Validé sur 2 projets distincts : todo-batch-alpha + personal-blog (Option B)

FIXES RÉELLEMENT APPLIQUÉS (en plus des acquis v2.0) :
  Fix 9  — dev_test_agent.py : success = build_success (découplé tests_passed)
           → tests non bloquants, signal qualité dans metadata
  Fix 10 — todo_pilot_workflow.py : build_status="SUCCESS" basé sur dev_phase_success
           uniquement (tests_phase_success retiré du calcul)
  Fix 11 — shared_tools.py write_file() : lstrip("./") → startswith("./")
           → préserve le "." de ".env.local" (bug silencieux)
  Fix 12 — dev_test_agent.py : exclusion templated_files du contexte test agent
           → test_coverage_agent reçoit uniquement fichiers business testables
  Fix 13 — Template tests/middleware.test.ts créé : test structurel exports-only
           pour Edge Runtime Clerk v6 — toujours vert, jamais écrasable
  Fix 14 — shared_tools.py run_tests() : guard vérifie templated_files avant écriture
           → protège les templates contre l'écrasement LLM

ACQUIS RÉELS SPRINT 2 (mis à jour 03 Mars 2026) :
  ✅ Pipeline end-to-end Architect→Dev→QA→GitHub→Learner
  ✅ 12-14 fichiers générés par run (dont 2 tests LLM + 1 template middleware)
  ✅ RAG actif avec k=5, 64 standards
  ✅ Sanitizers : Clerk fix, VERSION_PINS, middleware V4→V5
  ✅ Séparation workflow_status / build_status
  ✅ Fix App Router/Pages Router (_remove_pages_router_conflicts)
  ✅ Learner shadow : 44 events cumulés (requirement ≥3 : FAR EXCEEDED)
  ✅ Stack-as-Config : dev_packages, spec_validation, templates, templated_files
  ✅ Fix EJSONPARSE, Fix Phase 1→2, Fix Clerk v6, Audit Version-Semantic Drift
  ✅ clerk_compliant=true + semantic_violations=[] reproductibles
  ✅ build_success=true + tests_passed=true sur même run (Run 578623e6)
  ✅ Casing conflit résolu : tsconfig.json exclut tests/** du build TypeScript
  ✅ Stack-as-Config JSON 9.2/10 : forbidden_imports, import_remaps, mandatory_rag_queries,
     compatibility_matrix, templated_files, blueprint, qdrant_filter, prompt_rules

CONFIG-RUNTIME DRIFT IDENTIFIÉ (non bloquant Sprint 2, à corriger Sprint 3) :
  ⚠️ qdrant_filter déclaré dans JSON → ignoré par rag_search() (bruit cross-stack)
  ⚠️ commands.install/build déclarés → run_build() hardcode "npm install"/"npm run build"
  ⚠️ LearnerActivity génère suggestions hardcodées (total_files < 8) au lieu de lire shadow log

---

## SPRINT 3 — Stabilisation + Fondations Modularité
## Deadline : 7 Mars 2026 | STATUT : ✅ COMPLÉTÉ — 04 Mars 2026

OBJECTIF : Poser les fondations qui rendront chaque sprint suivant
plus facile à construire. Pas de nouvelles features sur base instable.

DÉJÀ ACCOMPLI (avant démarrage officiel Sprint 3, anticipé en Sprint 2) :
  ✅ Stack-as-Config JSON complet (9.2/10 — config/stacks/nextjs-clerk-prisma.json)
  ✅ templated_files system : fichiers protégés déclarés dans JSON, jamais écrasables
  ✅ blueprint + required_files opérationnels
  ✅ tsconfig.json exclut tests/** (fix casing Phase A-bis déjà résolu)
  ✅ stack_config.py loader — lecture JSON + get_root_file() multi-stack ready
  ✅ run_id propagé via context.py (ContextVar async-safe)
  ✅ Learner shadow log actif : 44 events cumulés sur 2 projets

RESTE À FAIRE SPRINT 3 (par priorité) :

### Phase A — Sécurité + Nettoyage (J1-J2) [PRIORITÉ 🔴]

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
   - Supprimer dead code : prompts/architect.md, prompts/dev.md (jamais chargés)

3. CENTRALISER PROMPT LOADER :
   - architect.py, qa.py, test_coverage.py 
     → tous via utils/prompt_loader.py
   - Zéro loader custom par agent

### Phase A-bis — Fix Bloqueur Casing ✅ RÉSOLU EN SPRINT 2

PROBLÈME INITIAL : Sur Linux (filesystem case-sensitive), conflit de casse
entre Layout.test.tsx et layout.test.tsx → TypeScript refusait de compiler.

RÉSOLUTION APPLIQUÉE (Sprint 2, avant démarrage Sprint 3) :
  ✅ FIX 2 appliqué : tsconfig.json template exclut "tests/**" du build TypeScript next
     → Jest compile les tests séparément, next build ne les voit plus
     → plus de conflit de casse possible au niveau TypeScript
  NOTE : FIX 1 (normalisation lowercase) non nécessaire car FIX 2 suffit.
  Le template tsconfig.json est protégé par templated_files → jamais écrasé.

### Phase B — Stack-as-Config (J3-J5) [PRIORITÉ 🔴 — Config-Runtime Drift]

PRINCIPE : Extraire toutes les règles stack-spécifiques du code Python
vers un fichier de configuration déclaratif.

ÉTAT ACTUEL (03 Mars 2026) :
  ✅ config/stacks/nextjs-clerk-prisma.json existe et est opérationnel (9.2/10)
  ✅ packages, dev_packages, forbidden_*, import_remaps, templated_files, blueprint
  ✅ mandatory_rag_queries, compatibility_matrix, version_pins, prompt_rules
  ❌ qdrant_filter NON branché dans rag_search() → bruit cross-stack (shadcn, etc.)
  ❌ commands.install/build NON lus dans run_build() → hardcodé "npm install"
  ❌ primary_manifest non défini (hardcodé "package.json" dans dev.py)
  ❌ cleanup_exclude non défini (hardcodé "node_modules" dans shared_tools.py)

ACTIONS RESTANTES PHASE B :

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

  1. qdrant_filter : déclaré dans JSON, ignoré par rag_search() [🔴 SPRINT 3]
     → rag_search retourne des standards de toutes les stacks (noise shadcn, etc.)
     → FIX Sprint 3 : brancher qdrant_filter dans rag_search() via stack_cfg
     → IMPACT : élimination du noise cross-stack dans les résultats RAG

  2. commands : déclaré dans JSON, run_build() hardcode "npm install" + "npm run build" [🔴 SPRINT 3]
     → FIX Sprint 3 : run_build() lit commands.install et commands.build depuis stack_cfg
     → IMPACT : finalise Stack-as-Config pour la couche d'exécution
     → BONUS : prépare multi-stack (Python/FastAPI → "pip install -r requirements.txt")

  3. test_import_rules : déclaré dans JSON, non branché dans les agents [🟡 SPRINT 4]
     → FIX Sprint 4 (moins critique) : brancher dans test_coverage.py

  4. primary_manifest + cleanup_exclude : non déclarés dans JSON [🟡 SPRINT 3/4]
     → Actuellement hardcodés "package.json" et "node_modules" dans dev.py/shared_tools.py
     → À déclarer dans JSON pour préparer stacks non-Node (Python, Go, Rust)

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

SIGNAL CLÔTURE SPRINT 3 — 04 Mars 2026 :
  ✅ build_success=true reproductible (7 runs consécutifs, 2 projets distincts)
  ✅ config/stacks/nextjs-clerk-prisma.json actif (9.2/10)
  ✅ qdrant_filter branché dans rag_search() via _json_filter_to_qdrant()
  ✅ commands.install/build lus depuis JSON dans run_build()
  ✅ commands.test lu depuis JSON dans run_tests() [Audit Fix A]
  ✅ primary_manifest + cleanup_artifacts dans JSON + retrait hardcoding dev.py
  ✅ LearnerActivity lit learner_shadow_log.json + génère 5 StandardSuggestion (run 04 Mars)
  ✅ validate_config_consumption.py opérationnel (scripts/validate_config_consumption.py)
  ✅ env_validation_regex (env_validation) ajouté dans JSON stack
  ✅ tag_qdrant_standards.py corrigé (nested metadata, non flat keys)
  ✅ AgentState architect : run_id + stack_id déclarés formellement [Audit Fix B]
  ✅ Architect retrieval_node : filtre stack appliqué (_build_architect_rag_filter) [Audit Fix B]
  ✅ test_sprint3_validation.py créé (7 blocs, 30 tests statiques) [Audit Fix C]
  ⚠️  64 standards Qdrant à tagger via reset_qdrant.py + create_full_standards_v1.py (procédure manuelle)
  ⚠️  VERSION_PINS non supprimé du code Python (décision : garder comme safety net, non bloquant)
  ⚠️  Secrets rotation + .gitignore : recommandé mais hors scope code (action DevOps)
  ⚠️  Prompt loader centralisé : reporté Sprint 4 (non bloquant)
  ⚠️  test_sprint1_validation.py : déclassé legacy (non-bloquant, Sprint 1 artefacts) — reporté archivage Sprint 4

AUDIT EXTERNE (04 Mars 2026 — Codex) :
  Audit indépendant post-Sprint 3 — 3 non-conformités corrigées immédiatement :
  Audit Fix A — commands.test non consommé : run_tests() hardcodait npx jest
    → FIX : run_tests() lit commands.test depuis JSON + append --passWithNoTests si absent
  Audit Fix B — Architect sans contrat run_id/stack_id ni filtre RAG stack :
    → FIX : AgentState TypedDict + _build_architect_rag_filter() + vectorstore.asimilarity_search(filter=)
  Audit Fix C — Quality gates alignés sur Sprint 1 artefacts inexistants :
    → FIX : tests/test_sprint3_validation.py — 7 blocs couvrant l'état réel Sprint 3
  Restant à traiter Sprint 4 (non critique) :
    → test_sprint1_validation.py archivé comme legacy
    → env_validation regex branché dans le code runtime
    → validate_config_consumption.py : validation par composant (pas juste regex globale)

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
## Deadline : Mars 2026 | STATUT : ✅ COMPLÉTÉ (Groupes A-D accomplis — voir MEMORY.md)

OBJECTIF : Valider empiriquement l'architecture + fermer la boucle
d'apprentissage + préparer multi-stack

### Groupe A — Spec Coverage + Architect (fondation)

1. ARCHITECT PROMPT FIX :
   Ajouter prompt_rules dans nextjs-clerk-prisma.json pour forcer
   l'Architect à extraire TOUS les requirements du brief (modèles,
   pages, routes, champs). Aujourd'hui l'Architect génère un spec
   auth générique en ignorant les détails métier du brief.
   OUTPUT : champ requirements[] dans l'output Architect.

2. CONTRACTS INTER-AGENTS v2 :
   Architect Output Contract v2 — champs OBLIGATOIRES :
   {
     "router_type": "app",
     "stack_id": "nextjs-clerk-prisma",
     "requirements": ["Post model", "/blog/[slug]", "PUT /api/posts/[id]"],
     "forbidden_paths": [...],
     "required_files": [...]
   }
   Si un champ manque → refus de passer à DevAgent.

3. SPEC_COVERAGE SCRIPT :
   Script Python générique (pas un agent) qui compare :
     requirements[] (déclaré par Architect)
     vs combined_files (générés par DevAgent)
   Calcule un pourcentage : spec_coverage = requirements_met / total
   Loggé dans dev_test_run event du shadow log.
   Dépend de #1 (requiert le champ requirements dans l'output Architect).

### Groupe B — Qualité génération

4. BLUEPRINT VALIDATOR BLOQUANT :
   Passer de WARNING (Sprint 3) à BLOQUANT :
   Si required_files manquants → DevAgent itère jusqu'à complétion
   avant de lancer run_build. Le build n'est jamais lancé sur une
   base incomplète.

5. QA AGENT FIX :
   Passer combined_files comme contexte au QA agent.
   Les tests E2E générés doivent vérifier les routes et pages
   réellement présentes dans combined_files — plus de tests
   fantômes pour des routes non générées.

### Groupe C — Boucle d'apprentissage

6. ANTI-PATTERNS AUTOMATIQUES :
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
   Ces anti-patterns sont récupérés en priorité haute dans rag_search.

7. APPROVE_SUGGESTION.PY :
   Script ~30 lignes. L'humain lit learner_suggestions.json,
   tape y/n pour chaque suggestion. Les suggestions approuvées
   sont upsertées dans Qdrant avec status=active.
   SLA : review dans les 48h max (sinon boucle d'apprentissage bloquée).

8. QDRANT GOVERNANCE v1 :
   Standards avec status: active | deprecated | archived.
   Quand un standard est superseded : ancien passe à deprecated.
   Qdrant ne retourne que status=active.
   {
     "id": "clerk-auth-v5",
     "version": "2.0",
     "supersedes": "clerk-auth-v4",
     "status": "active",
     "valid_from": "2026-02-23"
   }

9. GATE DÉCISIONNEL :
   Review LearnerAgent suggestions (15-20 cumulées).
   Validation humaine >70% → activation mode actif Sprint 5.
   Baseline mobile 3 projets activée.

### Groupe D — Residuels Audit Sprint 3 (non bloquants)

10. env_validation regex branché dans le code runtime
11. test_sprint1_validation.py archivé comme legacy
12. validate_config_consumption.py : validation par composant
    (pas juste regex globale — vérifier que chaque champ JSON
    est effectivement consommé par son composant responsable)

SIGNAL CLÔTURE SPRINT 4 :
  - 3 projets avec build_success=true ET spec_coverage > 0%
  - Blueprint Validator BLOQUANT opérationnel
  - Contracts inter-agents v2 validés (requirements[] present)
  - Anti-patterns créés automatiquement par LearnerAgent
  - approve_suggestion.py opérationnel avec SLA 48h
  - LearnerAgent : >15 suggestions générées
  - Suggestions validées >70% → Sprint 5 activé

---

## SPRINT 4.5 — Couche Valeur Client
## Deadline : Après Sprint 4 | STATUT : Planifié

CONTEXTE : Sprint 4 = "est-ce que ça build ?"
           Sprint 4.5 = "est-ce que l'utilisateur peut réellement s'en servir ?"

La factory génère du code qui compile, mais pas forcément une app
qui répond au besoin du brief. Sprint 4.5 mesure la valeur perçue.

Ce que ce n'est PAS :
  - Playwright/E2E complet (Sprint 6)
  - Déploiement Vercel (Sprint 6)
  - Tests manuels humains

Ce que c'est :

1. USER JOURNEY SPEC (extension de l'Architect) :
   L'Architect extrait en plus des requirements[] les user_flows[] :
   Exemple brief "Blog CMS" :
   {
     "user_flows": [
       "Visiteur lit la liste des posts publiés sur /",
       "Visiteur lit un post sur /blog/[slug]",
       "Auteur crée un post depuis le dashboard",
       "Auteur publie/dépublie un post via PUT /api/posts/[id]"
     ]
   }

2. JOURNEY VALIDATOR (script déterministe) :
   Pour chaque user_flow, vérifie qu'une route correspondante
   existe dans combined_files.
   Exemple :
     "lit un post sur /blog/[slug]" → cherche app/blog/[slug]/page.tsx
     "PUT /api/posts/[id]" → cherche app/api/posts/[id]/route.ts
   Produit : user_flows_covered = N/total

3. SEUIL DE VALEUR :
   spec_coverage > 80% ET user_flows_covered > 60% = "app utile"
   Loggé dans le shadow log comme métrique de valeur client.

SIGNAL CLÔTURE SPRINT 4.5 :
  - user_flows[] extrait par l'Architect sur 3 projets distincts
  - Journey Validator opérationnel et logge dans shadow log
  - Au moins 1 projet atteint spec_coverage > 80%

---

## PRÉ-SPRINT 4.6 — Refactoring Architect Agent (fondation Sprint 4.6+)
## Deadline : Avant Sprint 4.6 | STATUT : ✅ ABSORBÉ par Refactorisation Architecture Simplifiée (Phase A — 27-28 Mars 2026)

CONTEXTE :
  L'Architect Agent a accumulé des incohérences architecturales au fil des sprints :
  - requirements[] trusté depuis le LLM (source d'erreur) au lieu d'être dérivé déterministiquement
  - DEGRADED correction loop (3 appels LLM) corrigeant un contrat lui-même faux
  - Diagrammer dans le pipeline principal (jamais utilisé par le DevAgent)
  - Entités du brief injectées APRÈS le contexte RAG → biais de position LLM
  - Absence de normalisation du brief → planner dérive sur briefs en prose naturelle
  Ces dettes produisaient des "ghost success" : BUILD_SUCCESS avec la mauvaise app.

OBJECTIF :
  Repartir sur des fondations propres AVANT d'ajouter l'Agent Critique.
  Un Agent Critique comparant des requirements[] LLM-générés (potentiellement faux)
  n'apporte aucune valeur. La fiabilité du contrat requirements[] est un prérequis.

ARCHITECTURE CIBLE (graph LangGraph) :

  START
    ↓
  [brief_normalizer]  — gpt-4o-mini, ZÉRO RAG
    ↓                   Transforme tout brief (prose/structuré) en brief normalisé
  [retrieval]         — Qdrant, query = normalized_brief (pas de LLM rewriting séparé)
    ↓                   Retourne RAG context filtré par stack + status=active
  [planner]           — gpt-4o, normalized_brief + rag_context
    ↓                   Produit plan{} : data_models, pages, api_routes, user_flows
  [spec_writer]       — gpt-4o-mini, plan{} + deterministic requirements[] + rag_context
    ↓                   1 appel LLM + auth check + stack keywords check
  [formatter]         — 0 LLM, pack ArchitectOutput
    ↓
  END

PRINCIPE CLÉ — Brief Normalizer :
  Input  : brief utilisateur (n'importe quel format)
  Output : brief structuré avec blocs Prisma explicites, pages, routes
  Raison : sépare "ce qu'on construit" (domaine métier = LLM natif)
           de "comment on le construit" (patterns stack = RAG)
  Multi-stack : aucune dépendance stack — extrait uniquement le domaine métier

PRINCIPE CLÉ — requirements[] déterministe :
  TOUJOURS dérivé de plan.data_models / plan.pages / plan.api_routes
  JAMAIS depuis plan["requirements"] (champ LLM-généré, source de ghost success)
  Garantit que l'Agent Critique (Sprint 4.6) compare contre un contrat fiable

ÉLÉMENTS SUPPRIMÉS :
  - diagrammer_node retiré du graph (jamais utilisé par DevAgent, 30s timeout)
  - DEGRADED correction loop supprimée de spec_writer (validait un contrat faux)
  - sprint5_gate dans spec_writer (mauvais endroit, logique future)
  - plan["requirements"] comme source de requirements[] (remplacé par dérivé déterministe)
  - Query rewriting LLM séparé (remplacé par usage direct du normalized_brief)

ÉLÉMENTS CONSERVÉS :
  - _contains_forbidden_auth (stack-specific, légitime)
  - Stack keywords/sections check (stack-specific, légitime)
  - _build_minimal_plan_from_phrase (fallback déterministe si JSON invalide)
  - RAG filter par stack + status=active (inchangé)
  - user_flows[] extraction du plan (inchangé)
  - Journey Validator en aval (inchangé)

COÛT LLM :
  Avant refactoring : 4 appels nominaux, 9 appels pire cas
  Après refactoring  : 3 appels nominaux (normalizer + planner + spec_writer), 5 pire cas

SIGNAL CLÔTURE PRÉ-SPRINT 4.6 :
  - brief_normalizer opérationnel (test sur 3 briefs prose + 3 briefs structurés)
  - requirements[] 100% déterministe (zero LLM hallucination dans le contrat)
  - Ghost success impossible (requirements[] reflète toujours le plan réel)
  - reveal tests : marketplace-mvp + habit-tracker + invoice-generator → BUILD_SUCCESS
    avec les BONNES entités générées (Product/Order, Habit/HabitLog, Client/Invoice)

---

## SPRINT 4.6 — Supervision Inline : Système Multi-Agents (v2 — 20 Mars 2026)
## Deadline : Après Sprint 4.5 | STATUT : ❌ ABANDONNÉ — 27-28 Mars 2026
##
## ⚠️ ATTENTION : L'architecture décrite ci-dessous (conformity_activity, security_activity,
## architecture_activity en parallèle) a été EXPLICITEMENT DÉPRÉCIÉE par la Refactorisation
## Architecture Simplifiée (Phase C, 27-28 Mars 2026).
## Les agents conformity_agent.py, security_agent.py, architecture_agent.py sont marqués
## DÉPRÉCIÉS dans le code. Ne PAS implémenter cette architecture.
## La supervision est désormais déterministe uniquement : tsc + eslint.
## Conservation de cette section pour historique uniquement.

CONTEXTE :
  Sprint 4   = "est-ce que ça build ?"
  Sprint 4.5 = "est-ce que l'app répond au brief ?"
  Sprint 4.6 = "est-ce que chaque fichier généré respecte le brief, est sécurisé
               et cohérent — avant même de passer au fichier suivant ?"

PHILOSOPHIE (v2 — révisée 20 Mars 2026) :
  La v1 décrivait un reviewer post-génération. C'était insuffisant.
  La vision correcte : des superviseurs inline qui observent le Dev fichier par fichier,
  corrigent chirurgicalement, et laissent le build valider uniquement la compilabilité.

  PRINCIPE FONDAMENTAL :
    Dev écrit un fichier → Superviseur(s) observent → correction ciblée si besoin
    → fichier suivant. Pas de restart complet. Pas de revue globale tardive.

  FIN DES GUARDS DÉTERMINISTES :
    Les guards regex dans shared_tools.py sont supprimés (code mort avec cette architecture).
    Les compilateurs (tsc, prisma validate, next build) sont les seuls arbitres d'intégrité.
    Les superviseurs LLM sont les arbitres de qualité, conformité et sécurité.
    Le Learner + RAG sont les arbitres de prévention sur le long terme.

  CONFORMITÉ = STRUCTURE + SENS :
    Un superviseur ne vérifie pas seulement qu'un fichier EXISTE à la bonne route.
    Il vérifie que le CONTENU du fichier implémente réellement ce que le brief demande.
    Exemple : brief "marketplace" → le superviseur vérifie que app/api/orders/route.ts
    crée bien une commande avec productId + buyerId + quantity, pas juste qu'il existe.

ARCHITECTURE — SUPERVISION INLINE PAR TYPE DE FICHIER :

  ┌─────────────────────────────────────────────────────────────────────┐
  │  Pour chaque fichier généré par write_file() :                      │
  │                                                                     │
  │  *.tsx pages           → Superviseur Conformité Sémantique          │
  │  app/api/**/*.ts       → Superviseur Conformité + Superviseur Sécu  │
  │  prisma/schema.prisma  → Superviseur Cohérence Architecturale       │
  │  lib/*.ts, utils/*.ts  → Superviseur Conformité (léger)             │
  │  Templates protégés    → Pas de supervision (immuables)             │
  │                                                                     │
  │  Si superviseur détecte problème (confidence > 0.7) :               │
  │    → Instruction chirurgicale envoyée au Dev                        │
  │    → Dev corrige CE FICHIER UNIQUEMENT                              │
  │    → Superviseur re-vérifie → si OK, fichier suivant                │
  └─────────────────────────────────────────────────────────────────────┘

  APRÈS tous les fichiers :
    [tsc --noEmit] + [prisma validate] → erreurs résiduelles → Superviseur Compilabilité
    → instruction ciblée au Dev (ligne précise, pas restart)
    → Build final → QA → GitHub

LES 3 SUPERVISEURS CORE (chacun avec sa Temporal Activity) :

  SUPERVISEUR CONFORMITÉ SÉMANTIQUE (conformity_activity)
  ────────────────────────────────────────────────────────
  Input  : fichier_path + contenu + requirements[] + plan{} (contexte projet complet)
           + tous les fichiers générés jusqu'ici (contexte cumulatif)
  Tâche  : DEUX NIVEAUX de vérification :
    1. Structurel : ce fichier couvre-t-il le requirement attendu ? (route, modèle, page)
    2. Sémantique : le CONTENU du fichier fait-il réellement ce que le brief demande ?
       - La page `/products` AFFICHE-T-ELLE des produits avec prix + bouton achat ?
       - Le handler POST `/api/orders` CRÉE-T-IL une commande avec productId + buyerId ?
       - Le dashboard FILTRE-T-IL par authorId ou expose-t-il toutes les données ?
  Output : {
    "status": "ok|needs_fix",
    "confidence": 0.85,
    "fix_instruction": {
      "file": "app/products/page.tsx",
      "problem": "La page affiche une liste statique, sans fetch des produits depuis l'API",
      "fix": "Ajouter un appel fetch('/api/products') et mapper les résultats en JSX",
      "lines_concerned": [12, 28]
    }
  }
  RAG    : ZONE_15 — exemples de conformité structurelle ET sémantique
  Prompt : prompts/base/conformity.md + prompts/stacks/<stack>/rules_conformity.md

  SUPERVISEUR SÉCURITÉ (security_activity)
  ─────────────────────────────────────────
  Input  : fichier_path + contenu (routes API uniquement)
           + schema Prisma (contexte des modèles et leurs champs sensibles)
  Tâche  : pour chaque handler détecté dans le fichier :
    1. Auth check présent avant toute opération Prisma
    2. Queries filtrées par authorId (pas d'exposition cross-user)
    3. Pas d'exposition de champs sensibles
    4. Input validation sur POST/PUT
  Output : {
    "status": "ok|needs_fix",
    "confidence": 0.90,
    "fix_instruction": {
      "file": "app/api/orders/route.ts",
      "handler": "POST",
      "problem": "Aucun auth() check avant db.order.create()",
      "fix": "Ajouter : const { userId } = await auth(); if (!userId) return Response.json({error:'Unauthorized'},{status:401}); en ligne 3",
      "lines_concerned": [3]
    }
  }
  RAG    : ZONE_16 — patterns sécurité Clerk v6 valides/invalides avec code
  Prompt : prompts/base/security.md + prompts/stacks/<stack>/rules_security.md

  SUPERVISEUR COHÉRENCE ARCHITECTURALE (architecture_activity)
  ─────────────────────────────────────────────────────────────
  Input  : fichier_path + contenu + schema Prisma + plan{} (data_models, relations)
  Tâche  : vérifier que le fichier est cohérent avec le schéma de données global
    - Un composant Orders utilise-t-il bien la relation Order→Product pour afficher
      le nom du produit, ou affiche-t-il juste l'ID ?
    - Un route handler crée-t-il les champs obligatoires du modèle Prisma (createdAt, authorId) ?
    - Les imports entre fichiers sont-ils valides (path qui existe dans combined_files) ?
  Output : même format que Conformité (status/confidence/fix_instruction)
  RAG    : ZONE_15 (partagé avec Conformité) — patterns de cohérence inter-fichiers
  Prompt : prompts/base/architecture.md + prompts/stacks/<stack>/rules_architecture.md

  SUPERVISEUR COMPILABILITÉ (build_supervisor_activity) — POST-BUILD UNIQUEMENT
  ────────────────────────────────────────────────────────────────────────────────
  Déclenché uniquement si le build échoue.
  Input  : stderr du build + combined_files
  Tâche  : identifier le(s) fichier(s) et ligne(s) responsables de l'erreur
           → instruction ciblée au Dev pour corriger UNIQUEMENT cette zone
           → le Dev ne repasse PAS par les autres superviseurs (déjà validés)
  Output : {
    "failing_file": "app/products/[id]/page.tsx",
    "error_type": "TypeScript",
    "fix_instruction": "..."
  }

SUPERVISION BUDGÉTISÉE — RÈGLE D'ACTIVATION :
  Ne pas appeler tous les superviseurs sur chaque fichier.
  Routing par type de fichier (déclaré dans stack JSON) :
  {
    "supervision_routing": {
      "app/api/**/*.ts":      ["conformity", "security"],
      "app/**/*.tsx":         ["conformity", "architecture"],
      "prisma/schema.prisma": ["architecture"],
      "lib/**/*.ts":          ["conformity"],
      "**/*.test.*":          []
    }
  }

SCORE DE CONFIANCE — RÈGLE D'APPLICATION :
  confidence > 0.8 → correction obligatoire (bloque le fichier suivant)
  confidence 0.6-0.8 → correction suggérée (Dev peut passer outre, logué)
  confidence < 0.6 → observation uniquement, transmis au Learner

INSTRUCTION CHIRURGICALE — FORMAT OBLIGATOIRE :
  Toute correction doit spécifier :
    file, problem (description précise), fix (code ou instruction exacte),
    lines_concerned (lignes à modifier)
  Interdire les instructions vagues comme "corrige l'auth" ou "améliore la page".

SUPERVISION MEMORY DANS LE RUN :
  Le Superviseur Conformité maintient une vue cumulative du projet en cours :
  - Fichiers déjà vérifiés et leur statut
  - Requirements déjà couverts vs manquants
  - Patterns détectés (ex: "le Dev n'utilise jamais les types TypeScript → signaler tôt")
  Cette mémoire permet d'anticiper et de contextualiser chaque nouveau fichier.

TEMPORAL ACTIVITIES — VISIBILITÉ DASHBOARD :
  Chaque superviseur est une Temporal Activity indépendante :
  - conformity_activity   → visible sur le dashboard Temporal
  - security_activity     → visible sur le dashboard Temporal
  - architecture_activity → visible sur le dashboard Temporal
  - build_supervisor_activity → visible sur le dashboard Temporal (si build échoue)
  Le Dev loop (dev_test_activity) les appelle via execute_activity().

RISQUES MULTI-AGENTS ET MITIGATIONS :

  1. COÛT TOKENS
     Risque   : 2-3 appels LLM/fichier × 20 fichiers = 40-60 calls/run supplémentaires
     Mitigation :
       - Supervision budgétisée (routing par type de fichier)
       - Modèle gpt-4o-mini pour tous les superviseurs (pas gpt-4o)
       - Skip si fichier = template protégé ou fichier de config
       - Caching : si contenu identique à un template → supervision sautée

  2. HALLUCINATION SUPERVISEUR
     Risque   : superviseur déclare un fichier défaillant alors qu'il est correct
     Mitigation :
       - Score de confiance obligatoire dans chaque output
       - Correction non-bloquante si confidence < 0.7
       - Learner track les faux positifs (superviseur corrige → build réussit quand même)
         → recalibration automatique du prompt superviseur

  3. MANQUE DE CONNAISSANCE RAG
     Risque   : superviseur ne connaît pas les patterns Clerk v6 → mauvais verdict
     Mitigation :
       - Chaque superviseur fait sa propre query RAG (ZONE_15/16) avant de juger
       - Standards prescriptifs ZONE_15/16 avec EXEMPLE_INVALIDE + EXEMPLE_VALIDE
       - Si RAG retourne 0 résultats → superviseur passe en mode "observation uniquement"

  4. CALIBRATION PROMPTS
     Risque   : superviseur trop sévère → Dev corrige indéfiniment
     Mitigation :
       - Calibration sur 10 runs avant activation en mode bloquant
       - Seuil de confiance progressif (0.9 en phase calibration, 0.7 en production)
       - Learner mesure le ratio corrections→succès build : si <60% → prompt recalibré

  5. MULTI-STACK
     Risque   : superviseurs codés pour Next.js/Clerk → inutiles pour Vue/FastAPI
     Mitigation :
       - Même architecture Stack-as-Config : supervision_routing déclaré dans JSON
       - prompts/stacks/<stack>/rules_conformity.md + rules_security.md + rules_architecture.md
       - Les prompts base sont stack-agnostiques (logique) ; les rules_ sont stack-specific

NETTOYAGE PRÉREQUIS — AVANT IMPLÉMENTATION :
  Supprimer de shared_tools.py :
    - Tous les content_guards (blocking + non-blocking) → remplacés par superviseurs
    - _sanitize_package_json_content() → Learner+RAG prévient, superviseur corrige
    - _sanitize_nextconfig_content() → superviseur compilabilité
    - _apply_clerk_middleware_v5(), _remove_pages_router_conflicts(),
      _remove_problematic_babel_config() → Learner+RAG à la source
  Conserver :
    - Templates (package.json, middleware.ts, etc.) — infrastructure, pas des guards
    - run_build(), run_tests(), run_tsc_check(), run_prisma_validate() — outils d'exécution neutres
    - SANITIZER_REGISTRY → migré Sprint 6 SanitizerRegistry (dette connue)

CONNEXION AVEC LE LEARNER (boucle évolutive) :
  Superviseur détecte pattern récurrent sur N runs (ex: handler POST sans auth)
    → Learner génère suggestion ZONE_15 ou ZONE_16
    → Après validation humaine → upsert Qdrant status=active
    → Prochain run : RAG retourne le bon pattern → Dev génère correctement dès le début
    → Superviseur n'a plus rien à corriger sur ce pattern
  Objectif : les superviseurs ont de moins en moins de travail à mesure que le Dev apprend.
  Un superviseur qui ne détecte plus rien = une réussite, pas une inutilité.

  De plus, les superviseurs transmettent au Learner :
    - Les bons comportements du Dev (fichiers validés sans correction au premier essai)
    - Les mauvais comportements récurrents (même erreur sur plusieurs runs)
    → Le Learner construit un profil comportemental du Dev pour affiner les standards.

NOUVELLES MÉTRIQUES SHADOW LOG :
  Par fichier supervisé :
    - supervisor_type : "conformity|security|architecture|build"
    - file_path : chemin du fichier supervisé
    - status : "ok|corrected|skipped"
    - confidence : float 0-1
    - correction_applied : bool
  Par run :
    - conformity_score : float 0-1 (% fichiers conformes sémantiquement)
    - security_score   : float 0-1 (% handlers sécurisés)
    - architecture_score : float 0-1 (% fichiers cohérents avec le schéma)
    - supervisor_corrections_count : int (corrections appliquées pendant la génération)
    - build_corrections_count : int (corrections post-build)

SIGNAL CLÔTURE SPRINT 4.6 (v2) :
  - Guards déterministes supprimés de shared_tools.py (code mort éliminé)
  - 3 superviseurs core opérationnels avec Temporal Activities dédiées
  - Supervision inline active dans le Dev loop (après chaque write_file)
  - Instruction chirurgicale au format obligatoire (file + problem + fix + lines)
  - Score de confiance dans chaque output superviseur
  - supervision_routing déclaré dans nextjs-clerk-prisma.json
  - ZONE_15 + ZONE_16 + ZONE_17 (architecture) créées dans Qdrant (≥5 standards chacune)
  - Superviseur Compilabilité opérationnel (post-build, ciblé)
  - conformity_score > 0.75 ET security_score > 0.80 ET architecture_score > 0.70
    sur au moins 2 projets distincts
  - Métriques par fichier loggées dans shadow log

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

3. WEB SEARCH → STANDARD (StandardsMaintenanceAgent)

RÔLE ARCHITECTURAL :
  La web search n'aide pas le LLM à générer — elle maintient les standards Qdrant
  à jour quand les APIs évoluent (Version Drift). C'est une source de mise à jour
  des standards, pas une béquille de génération.

FLUX COMPLET :
  Learner détecte pattern récurrent (hook déclenché N fois) →
  StandardsMaintenanceAgent cherche sur le web →
  Génère standard prescriptif (ACTION/DETECTION_REGEX/EXEMPLE) →
  Validation humaine obligatoire →
  Upsert dans Qdrant avec status=active →
  Prochain run : RAG retourne le bon standard → LLM génère correctement →
  Hook concerné n'est plus déclenché → hook retiré (ou reste safety net)

DÉPENDANCE SÉQUENTIELLE :
  Mode Replay (item 1) DOIT être opérationnel avant web search.
  Sans Mode Replay, impossible de valider qu'un standard issu du web corrige
  effectivement le problème (on pourrait injecter un mauvais standard).

OUTIL RECOMMANDÉ : Tavily API (pip install tavily-python)
  - Conçu pour les agents IA (résultats extractibles directement)
  - Filtrage par domaine officiel : include_domains par technologie
  - Prix estimé : ~$5/1000 requêtes
  ALLOWLIST PAR TECHNOLOGIE :
    next.js   → ["nextjs.org", "github.com/vercel/next.js"]
    clerk     → ["clerk.com", "github.com/clerkinc"]
    prisma    → ["prisma.io", "github.com/prisma/prisma"]
    jest      → ["jestjs.io", "testing-library.com"]

ARCHITECTURE StandardsMaintenanceAgent :
  class StandardsMaintenanceAgent:
    async def refresh_standard(self, technology: str, trigger: str):
      # 1. Recherche ciblée sources officielles uniquement
      results = tavily.search(
        query=f"{technology} breaking changes 2026 correct usage",
        include_domains=ALLOWLIST[technology],
        max_results=3
      )
      # 2. LLM génère standard prescriptif depuis les résultats
      standard = llm.generate_standard(trigger, results)
      # 3. Mode Replay valide que le standard corrige le problème
      validated = mode_replay.validate(standard, failing_run_id)
      # 4. Écriture dans learner_suggestions.json (PAS Qdrant direct)
      write_to_suggestions(standard, validated=validated)
      # 5. Validation humaine avant upsert Qdrant

VALIDATION HUMAINE (comment ?) :
  Fichier: learner_suggestions.json
  Champs à vérifier :
    - EXEMPLE_INVALIDE : correspond-il exactement à ce que le LLM génère ?
    - EXEMPLE_VALIDE : buildé et testé manuellement ?
    - ERREUR_ATTENDUE : message d'erreur exact (pas approximatif) ?
    - source_url : lien vers doc officielle (Tavily cite ses sources)
  Action : si OK → python scripts/approve_suggestion.py <id> → upsert Qdrant

SIGNAL CLÔTURE SPRINT 5 :
  - Boucle RAG→Learner→RAG fermée et prouvée (≥1 upsert validé)
  - Mode Replay opérationnel
  - Compatibility matrix dans Qdrant (remplace VERSION_PINS total)
  - Tavily API intégré avec allowlist par technologie
  - StandardsMaintenanceAgent produit des suggestions dans learner_suggestions.json
  - approve_suggestion.py opérationnel (validation humaine → upsert Qdrant)
  - ≥1 hook supprimé grâce à un standard web-search validé

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

## 🎯 JALONS RÉVISÉS v2.1

| Date cible | Livrable | Signal mesurable | Statut |
|------------|----------|-----------------|--------|
| ~~Dès possible~~ | Sprint 2 clôturé | build_success=true + tests_passed=true reproductibles | ✅ 02 Mars 2026 |
| 7 Mars 2026 | Sprint 3 terminé | qdrant_filter branché + commands lus JSON + LearnerActivity connectée + standards taggés + secrets clean | ✅ 04 Mars 2026 |
| Fin Mars 2026 | Sprint 4 terminé | Gate décisionnel + anti-patterns auto + contracts inter-agents v2 | ⏳ |
| Début Avril 2026 | Sprint 4.5 | Journey Validator + user_flows + spec_coverage > 80% | ⏳ |
| Mi-Avril 2026 | Sprint 4.6 | Agent Critique (AgentConformité + AgentSécurité) + ZONE_15/16 | ⏳ |
| Fin Avril 2026 | Sprints 5-6 | Boucle RAG→Learner→RAG fermée + web search + dashboard gouvernance | ⏳ |
| Mi-Mai 2026 | Sprints 7-8 | Meta-learning + multi-stack <5% Python (Vue.js/FastAPI) | ⏳ |
| 15 Mai 2026 | Sprint 9 | Démo 50 projets autonomes | ⏳ |

DÉCISIONS ARCHITECTURALES PRISES (03 Mars 2026) :
  → Sprint 3 ≠ déploiement staging/Playwright/Vercel (c'est Sprint 6)
  → Sprint 3 = consolidation interne + fermeture Config-Runtime Drift
  → Focus marché : SaaS MVP (auth + CRUD + dashboard) — stack la plus homogène
  → Deuxième stack cible : e-commerce (Stripe) en Sprint 8, après multi-stack prouvé
  → Retry tenacity (shared_tools.py) : entre Sprint 3 et 4 (non bloquant mais ROI fort)
  → SanitizerRegistry : Sprint 6 exactement comme planifié v2.0
  → Vercel Preview Deploys + Playwright E2E : Sprint 6 (QA agent complet)

DÉCISIONS ARCHITECTURALES PRISES (18 Mars 2026) :
  → Guards regex → tous passés en mode WARN. TypeScript/Prisma/Next.js sont les
     arbitres autoritaires. Les guards informent, les compilateurs bloquent.
  → Agent Critique = 2 sous-agents LLM parallèles (Conformité + Sécurité) +
     2 outils déterministes (tsc --noEmit + prisma validate).
     TypeScript quality et Prisma patterns sont couverts par les outils → pas d'agent LLM pour ces dimensions.
  → ZONE_15 (conformity) + ZONE_16 (security) = nouvelles zones Qdrant à créer en Sprint 4.6.
  → La boucle Agent Critique → Learner → Standards → Dev est le moteur central
     de l'organisme évolutif : l'Agent Critique a pour objectif de se rendre inutile
     sur chaque pattern qu'il a appris à détecter.

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
#33 | Architecture | Guards regex → tous WARN. TypeScript/Prisma/Next.js sont arbitres autoritaires | Sprint 4.6 principe (18 Mars 2026)
#34 | Architecture | Agent Critique = AgentConformité + AgentSécurité (2 LLM parallèles) + tsc/prisma (2 outils) | Sprint 4.6
#35 | Standards    | ZONE_15 (conformity) + ZONE_16 (security applicative) créées dans Qdrant | Sprint 4.6
#36 | Évolution    | Boucle Agent Critique → Learner → ZONE_15/16 → Dev génère mieux → Agent Critique s'auto-rend inutile | Sprint 5+
#37 | Architecture | Brief Normalizer : nœud LangGraph dédié (gpt-4o-mini, zéro RAG) — sépare domaine métier (LLM natif) et patterns stack (RAG). Multi-stack by design. | Pré-Sprint 4.6
#38 | Architecture | requirements[] déterministe : TOUJOURS dérivé de plan.data_models/pages/api_routes — JAMAIS depuis plan["requirements"] LLM-généré. Élimine ghost success. | Pré-Sprint 4.6
#39 | Suppression  | diagrammer_node retiré du pipeline Architect (jamais utilisé par DevAgent, 30s timeout systématique). Conservé en fonction inactive pour Sprint 6 dashboard. | Pré-Sprint 4.6
#40 | Suppression  | DEGRADED correction loop supprimée de spec_writer (3 appels LLM pour corriger un contrat lui-même faux). Remplacée par observation pure. | Pré-Sprint 4.6
#41 | Fondation    | Pré-Sprint 4.6 est prérequis à Sprint 4.6 : Agent Critique comparant requirements[] fiables (déterministes) vs requirements[] LLM-générés (potentiellement faux) = valeur nulle. | 19 Mars 2026
#42 | Dette tech   | Moteur AST dans dev.py (guards `engine="ast"`) : placeholder non finalisé — loggé en TODO/skipped si binaire absent. Les protections avancées (analyse structurelle fichier avant write) ne sont pas effectives en production. À activer dans un sprint dédié si le besoin est confirmé. Fichier : `agents/dev.py` (grep `engine.*ast`). | Sprint 7+
#43 | Limite connue | Classes d'erreurs TypeScript — couverture partielle du feedback LLM : tsc est exhaustif (catch tous les codes), mais notre aide au LLM ne couvre que les classes observées en run réel. Classes traitées : TS2304/TS2724 (mauvais nom de type → A2+C2), TS2307 local (module manquant → E1). Classes non traitées : TS2322 (type incompatible), TS2339 (propriété inexistante), TS2307 npm (dépendance manquante). À traiter au fil des runs suivants — le Learner devra à terme enrichir les standards Qdrant pour que le LLM évite ces erreurs à la source. | Sprint 5+ Learner
#44 | Limite connue | Scalabilité brief complexe — budget tokens système prompt : chaque modèle Prisma ajoute ~300-500 chars au system prompt (schema block + types_block + checklist). Pour des briefs avec 8+ modèles fortement relationnels, risque de dégradation silencieuse : le LLM n'attende plus équitablement toutes les parties du prompt → certains modèles/routes ignorés. Seuil estimé : >6 modèles avec relations = zone à risque. Mitigation à prévoir Sprint 6-7 : prompt dynamique (injecter uniquement les modèles/routes liés au fichier en cours de génération, via contextualisation locale). Stack actuelle non affectée (briefs catalogue = 1-2 modèles). | Sprint 6-7