# RAPPORT DE BILAN — SOFTWARE AGENT FACTORY
## État du projet au terme du Sprint 2 vs Attentes

**Date de rédaction :** 22 Février 2026
**Branch analysée :** `fonc2`
**Dernière exécution documentée :** 23 Février 2026 — 00:02:24 UTC
**Audit de conformité :** OPERATIONAL_REALITY.md (conformité estimée : 49%)

---

## 1. RÉSUMÉ EXÉCUTIF

Le projet StartupNexus — Software Agent Factory arrive en fin de Sprint 2 avec une posture **ambitieuse mais partiellement tenue**. L'infrastructure de base est fonctionnelle et les agents tournent réellement en production, ce qui représente un acquis solide. Cependant, l'audit de conformité réalisé révèle un écart structurel de 51% entre les déclarations de la roadmap et la réalité opérationnelle, avec des trous critiques en observabilité RAG, en gouvernance runtime, et un risque de sécurité non résolu.

**Verdict global :**

| Dimension | Attendu Sprint 2 | Réalité observée | Delta |
|-----------|-----------------|-----------------|-------|
| Workflow de bout en bout | DONE | DONE (avec erreurs build) | ~OK |
| Code generation | 5 agents opérationnels | 5 agents actifs | OK |
| Couverture tests | >80% | 90-95% lignes | OK |
| 61 standards Qdrant | 61 standards | 64 en production | OK |
| LearnerAgent shadow mode | Agent dédié | Telémétrie seulement | PARTIEL |
| RAG observable | Traçabilité requise | Non traçable en prod | KO |
| Prompts centralisés | Tous agents | Dev seulement | PARTIEL |
| Secrets sécurisés | Obligatoire | Secrets exposés en clair | CRITIQUE |
| Docker healthchecks complets | Requis | Qdrant sans healthcheck | PARTIEL |

---

## 2. CE QUI EST RÉELLEMENT ACCOMPLI — LES POINTS FORTS

### 2.1 Infrastructure opérationnelle complète

Le stack Docker tourne avec 7 services inter-dépendants :
- **Temporal.io 1.29.1** — orchestration durable des workflows
- **Qdrant** — base vectorielle avec 64 standards chargés
- **PostgreSQL 17.7 + Elasticsearch 9.2.1** — backends Temporal
- **n8n** — interface humaine opérationnelle
- **Flask API (port 5000)** — point d'entrée REST

Le worker démarre proprement, se connecte à Qdrant, valide la collection et se met en écoute sur la queue `factory-task-queue`. C'est un démarrage robuste, confirmé dans les logs réels.

### 2.2 Pipeline de bout en bout exécuté

Le workflow `TodoPilotWorkflow` a effectivement tourné du 22 au 23 Février, avec la séquence complète :

```
Architect (44s) → DevTest (5min) → QA (6s) → GitHub (2min)
```

- Architect a généré 3223 caractères de spécification avec RAG k=10
- DevTest a généré **25 fichiers** (package.json, schema.prisma, middleware.ts, composants React, tests)
- QA a généré 1 fichier de tests E2E
- GitHub a poussé 26 fichiers et trouvé la PR existante

**Le pipeline de génération fonctionne réellement de bout en bout.** C'est l'accomplissement central de Sprint 2.

### 2.3 Défense à 2 niveaux — architecture solide

Le `shared_tools.py` implémente une architecture de défense en profondeur visible dans les logs :

**Niveau 1 — RAG/Prompt :**
- k=5 standards récupérés par requête (augmenté depuis k=2)
- Prompts chargés dynamiquement via `utils/prompt_loader.py` (pour Dev)
- Corpus de 64 standards opérationnels par catégorie (nextjs, clerk, prisma, testing, deployment)

**Niveau 2 — Garde-fous Tool :**
- `@clerk/clerk-sdk` → `@clerk/nextjs` automatiquement remappé
- `next@14.0.0` → `14.2.25` épinglé automatiquement
- Middleware `withClerkMiddleware` → `clerkMiddleware` (v4→v5) patché
- Dépendances test injectées (`jest-environment-jsdom`, `@testing-library/react`, etc.)
- `package.json` double-encodé détecté et corrigé

**9 types de patches loggués** avec le format `tool_patch_applied` — l'audit trail est partiellement opérationnel.

### 2.4 Contrats d'interface JSON Schema — maturité contractuelle

Les 5 contrats agents sont définis (Draft-07) avec 4 schémas chacun :
- `architect_agent_contract.json`
- `dev_agent_contract.json`
- `test_agent_contract.json`
- `qa_agent_contract.json`
- `github_agent_contract.json`

Validation runtime active : `✅ [architect_agent] Input valide` et `✅ [dev_test_agent] Input valide` sont confirmés dans les logs de production.

### 2.5 LearnerAgent shadow mode — télémétrie fonctionnelle

Même si ce n'est pas l'agent runtime attendu, la collecte de données existe :
- **9 events loggués par run** dans `logs/shadow/learner_shadow_log.json`
- Patterns détectés : `middleware_matcher`, `next_version`, `ts_jest_version`
- `avg_quality_score` = 13.8 (baseline observationnelle)
- Le chemin vers Sprint 5 (activation) est identifié

### 2.6 Documentation et roadmap de haute qualité

- Roadmap v1.5 (97% de cohérence interne)
- Audit opérationnel honnête (OPERATIONAL_REALITY.md) qui identifie les gaps réels
- Contrats d'interface formalisés
- Architecture à 3 couches (Code → Prompt → RAG) conceptuellement solide

---

## 3. LES PROBLÈMES — ANALYSE APPROFONDIE

### 3.1 CRITIQUE — Build non garanti en production

**Problème :** Le workflow termine avec `DevTest Success: False`. Le build Next.js échoue systématiquement sur le même conflit :

```
⨯ Conflicting app and page file was found:
⨯   "pages/index.tsx" - "app/page.tsx"
```

Le DevAgent génère des fichiers dans les deux paradigmes Next.js (Pages Router ET App Router) simultanément. L'erreur est reproductible, non corrigée entre les runs, et le workflow continue quand même vers QA et GitHub — ce qui signifie qu'on push du **code qui ne build pas**.

**Impact :** C'est une régression non résolue depuis au moins les 7 derniers runs (logs `todo_pilot_batch_*` du 22-23 Fév). Le workflow déclare `COMPLETED` mais `build_status` est `BUILD_FAILED`. L'absence de séparation sémantique `workflow_status` / `build_status` (prévu Sprint 3) masque l'ampleur du problème.

**Cause racine identifiée :** Le DevAgent consulte RAG puis génère du code mixant les deux conventions, probablement parce que les standards RAG ne distinguent pas clairement le contexte App Router exclusif. Les patches automatiques ne couvrent pas ce cas.

### 3.2 CRITIQUE — Secrets exposés dans le dépôt

**Problème :** Le fichier `.env` contient `OPENAI_API_KEY` et `GITHUB_TOKEN` en clair. L'audit OPERATIONAL_REALITY le classe en **CRITICAL** avec rotation immédiate requise.

**Impact :** Exposition des clés API et tokens GitHub dans l'historique git. Risque de compromission du compte OpenAI et du dépôt GitHub cible (`hounsouthohin/saas-todo-batch-alpha`).

**État :** Identifié le 17 Février, non résolu au 22 Février — 5 jours d'exposition documentée.

### 3.3 ÉLEVÉ — RAG non observable, conformité non mesurable

**Problème :** Les appels `rag_search` tournent (on le voit dans les logs HTTP), mais aucune trace structurée n'est écrite sur :
- quelle query exacte a été envoyée
- quels IDs de documents ont été retournés
- quels scores de similarité
- quel taux de couverture des 64 standards

**Conséquence directe :** Il est **impossible de prouver** que les 64 standards Qdrant influencent réellement les agents. On ne peut pas savoir si 5 standards sont utilisés à 90% et 59 ne sont jamais consultés.

**Ce qu'on voit dans les logs :**
```
[INFO] Executing rag_search with query: 'versions exactes next.js clerk prisma...'
HTTP Request: POST http://qdrant:6333/collections/factory_standards/points/query "200 OK"
```
Mais aucun log du résultat : IDs, scores, textes récupérés.

**Manque de KPI :** `standard_usage_rate = consulted_unique / total_standards` est non calculable.

### 3.4 ÉLEVÉ — Architecture layered partiellement respectée

**Problème :** Des versions sont hardcodées dans le code (`next=14.2.25`, `ts-jest=29.1.2`) alors que l'architecture déclare que ces détails doivent venir du RAG.

**Tension architecturale identifiée :** Il existe deux sources de vérité pour les mêmes règles :
- Prompt : "INTERDIT NextAuth, OBLIGATOIRE Clerk"
- RAG Standard : "Clerk authentication v5+ exclusive"

Le LearnerAgent (Sprint 5) ne pourra pas savoir si ses suggestions contredisent des règles hardcodées dans le prompt ou dans le code. La boucle d'apprentissage est conceptuellement cassée tant que cette dualité existe.

### 3.5 ÉLEVÉ — LearnerAgent non implémenté comme agent runtime

**Problème :** La roadmap v1.5 déclare `LearnerAgent (shadow)` comme livrable Sprint 2. La réalité :
- Il n'existe pas de fichier `agents/learner.py`
- Il n'existe pas de `LearnerActivity` dans le workflow Temporal
- Ce qui existe : une fonction `_write_learner_event()` dans `shared_tools.py` + un script `evaluator.py` hors workflow

**Impact Sprint 4-5 :** La validation shadow mode requise pour activer le LearnerAgent (>70% de pertinence sur 15-20 suggestions) ne peut pas être mesurée objectivement car les "suggestions" ne sont pas structurées — c'est de la télémétrie brute.

**Ce que dit l'audit :**
- LearnerAgent implémenté : **Partiellement**
- Shadow mode fonctionnel : **Oui (télémétrie)**
- Qualité suggestions : **Moyen à faible**
- Prêt activation Sprint 5 : **Non (avec corrections)**

### 3.6 MOYEN — Tests en échec structurel (24/41 suites failed)

**Problème :** Sur les 41 suites de tests générées, **24 échouent** à chaque run. Les 7-8 tests en échec sont récurrents et non corrigés entre les itérations :
- Confusion encodage Unicode (`Â©` au lieu de `©`) dans les assertions de texte
- Tests middleware Clerk qui attendent une API v4 (`auth().protect`) alors que le code est v5
- Tests API Next.js qui ne peuvent pas s'initialiser (`Cannot find module 'next/server'` dans le contexte Jest)

**Ce que cache la couverture :** La couverture de lignes de 90-95% est réelle mais trompeuse — elle mesure les lignes exécutées par les tests passants, pas la qualité des tests. 24 suites complètes sont inopérantes.

**Impact boucle d'apprentissage :** Le DevAgent ne corrige pas ces échecs entre les 10 itérations disponibles. L'historique est tronqué (`Historique trop long → truncation ultra-safe V3`) et les erreurs précédentes sont perdues.

### 3.7 MOYEN — Prompts non centralisés uniformément

**Problème :** Seul `dev.py` utilise `utils/prompt_loader.py`. Les agents `architect.py`, `qa.py`, `test_coverage.py` chargent leurs prompts directement avec des parseurs maison.

**Fichiers concernés :**
- `agents/architect.py:52` — loader custom
- `agents/qa.py:61` — lecture fichier directe
- `agents/test_coverage.py:112` — lecture fichier directe

**Impact :** Si on modifie un prompt, il faut connaître le mécanisme de chargement propre à chaque agent. Risque de désynchronisation silencieuse.

### 3.8 MOYEN — Vulnérabilité de sécurité dans les dépendances

**Ce que les logs révèlent :**
```
npm warn deprecated next@14.2.25: This version has a security vulnerability.
Please upgrade to a patched version. See https://nextjs.org/blog/security-update-2025-12-11
32 vulnerabilities (8 moderate, 24 high)
```

La factory **épingle délibérément** une version de Next.js qui est officiellement marquée comme vulnérable depuis Décembre 2025. Les projets générés héritent de 24 vulnérabilités HIGH dès leur création.

---

## 4. ÉCART ATTENDU vs RÉEL — SYNTHÈSE PAR LIVRABLE

### Sprint 2 — Livrables prévus (Roadmap v1.5)

| Livrable | Statut Roadmap | Statut Réel | Commentaire |
|----------|---------------|-------------|-------------|
| Code full-stack généré | ✅ | ⚠️ PARTIEL | 25 fichiers générés mais build KO |
| Tests unitaires | ✅ | ⚠️ PARTIEL | 41 suites, 24 failed |
| PR GitHub créée | ✅ | ✅ | PR créée et mise à jour |
| Coverage >80% | ✅ | ✅ | 90-95% lignes |
| Phase 1 validée | ✅ | ⚠️ PARTIEL | Voir audit 49% conformité |
| 61 standards Qdrant | ✅ | ✅ | 64 en production |
| LearnerAgent shadow | ✅ | ⚠️ PARTIEL | Télémétrie seulement |
| EvaluatorAgent observation | ✅ | ⚠️ PARTIEL | Script offline, pas activité |
| Corrections Phase 1 | ✅ DÉCLARÉ | ⚠️ PARTIEL | Prompts non centralisés, RAG non observable |
| Docker healthchecks | ✅ DÉCLARÉ | ⚠️ PARTIEL | Qdrant sans healthcheck |
| Secrets sécurisés | IMPLICITE | ❌ | Secrets exposés non rotés |

**Score Sprint 2 : 3 livrables complets / 5 partiels / 1 critique non résolu**

---

## 5. TENSIONS ARCHITECTURALES NON RÉSOLUES

### 5.1 Les patches masquent l'apprentissage

Les corrections automatiques dans `shared_tools.py` créent un paradoxe :
- Elles rendent le pipeline plus résilient (positif)
- Mais elles masquent les erreurs des agents au LearnerAgent (négatif)

Quand `write_file` corrige silencieusement `@clerk/clerk-sdk` → `@clerk/nextjs`, l'EvaluatorAgent voit un "succès" alors que l'agent a échoué. Le LearnerAgent ne peut pas proposer de renforcer le standard Clerk car l'erreur n'apparaît pas comme telle dans les métriques de résultat — seulement dans les logs de patch.

### 5.2 La séparation workflow_status / build_status est critique et absente

Actuellement, `TodoPilotWorkflow` retourne `COMPLETED` même si le build a échoué. Le pipeline pipeline continue vers QA et GitHub avec du code non compilable. La distinction sémantique prévue en Sprint 3 aurait dû être Sprint 2 selon l'urgence opérationnelle.

### 5.3 La boucle RAG → Prompt est en double

Les mêmes règles existent dans :
1. Les prompts (directives LLM)
2. Les standards Qdrant (récupérés par RAG)

Si on met à jour un standard Qdrant sans mettre à jour le prompt correspondant (ou vice-versa), on crée une incohérence invisible. L'architecture layered est documentée mais pas enforced par un mécanisme technique.

---

## 6. RISQUES POUR SPRINT 3

| Risque | Probabilité | Impact | Mitigation suggérée |
|--------|------------|--------|---------------------|
| Secrets non rotés → compromission | ÉLEVÉE | CRITIQUE | Rotation immédiate + gitignore strict |
| Build failure systématique → dette technique | ÉLEVÉE | ÉLEVÉ | Fix conflict pages/ vs app/ en priorité 0 |
| RAG non observable → KPI Sprint 3 non mesurables | ÉLEVÉE | ÉLEVÉ | Instrumenter rag_search avant Sprint 3 |
| 24 suites test failed → fausse baseline | ÉLEVÉE | MOYEN | Corriger les mocks Clerk + Next.js API |
| Vulnérabilité next@14.2.25 → projets générés vulnérables | ÉLEVÉE | MOYEN | Évaluer migration vers version patchée |
| LearnerAgent non prêt Sprint 5 | MOYENNE | ÉLEVÉ | Créer agents/learner.py et LearnerActivity maintenant |

---

## 7. RECOMMANDATIONS PRIORITAIRES

### P0 — À faire avant toute continuation (0.5j)
1. **Rotation IMMÉDIATE des secrets `.env`** (OPENAI_API_KEY, GITHUB_TOKEN)
2. **Ajouter `.env` au `.gitignore`** et auditer l'historique git

### P1 — À faire en début de Sprint 3 (3-4j)
3. **Fix conflict App Router vs Pages Router** — ajouter un garde-fou dans `write_file` ou les prompts pour interdire la génération de `pages/index.tsx` quand `app/page.tsx` existe
4. **Instrumenter `rag_search`** — logger `{run_id, agent, query, k, doc_ids, scores}` dans `logs/metrics/rag_usage.jsonl`
5. **Séparer `workflow_status` et `build_status`** dans le output de `TodoPilotWorkflow`
6. **Corriger les 24 suites de tests** — mocks Clerk v5, API Next.js dans Jest, encodage Unicode

### P2 — Dans Sprint 3 (2-3j)
7. **Centraliser tous les loaders de prompts** via `utils/prompt_loader.py` (Architect, QA, TestCoverage)
8. **Ajouter healthcheck Qdrant** dans docker-compose.yml + passer `factory-worker` en `service_healthy`
9. **Créer `agents/learner.py`** et `LearnerActivity` dans le workflow Temporal
10. **Évaluer Next.js 15** ou version patchée pour les projets générés

---

## 8. BILAN DE MATURITÉ PAR COMPOSANT

```
Infrastructure Docker     ████████░░  80%  — Opérationnel, Qdrant healthcheck manquant
Agents LLM               ████████░░  75%  — 5 actifs, pipeline end-to-end validé
Orchestration Temporal    █████████░  90%  — Workflows solides, retry configuré
Standards Qdrant          ████████░░  80%  — 64 standards, non observables en prod
Défense niv.2 (patches)  ████████░░  80%  — 9/10 patches loggués
Qualité code généré       ████░░░░░░  40%  — Build KO, 24 suites failed
RAG observabilité         ████░░░░░░  30%  — Appels fonctionnels, telémétrie absente
LearnerAgent              ████░░░░░░  35%  — Télémétrie brute, pas d'agent runtime
Sécurité                  ██░░░░░░░░  20%  — Secrets exposés, dépendances vulnérables
Prompts centralisés       ████░░░░░░  40%  — 1/4 agents conformes
```

---

## 9. CONCLUSION

Le projet démontre une **architecture conceptuellement solide** et une **ambition claire de long terme** (roadmap Sprint 9, 15 Mai 2026). Le pipeline de génération tourne réellement — c'est le succès central. Mais le Sprint 2 livre une infrastructure en état "beta fragile" plutôt qu'un livrable de production.

Les deux problèmes qui bloquent la progression saine vers Sprint 3 sont :

**1. Le build échoue de façon reproductible** — publier du code non compilable sur GitHub à chaque run est un défaut fondamental de la factory.

**2. Les secrets sont exposés depuis 5 jours** — ce risque de sécurité critique doit être résolu avant toute autre feature.

Tout le reste — tests partiellement échoués, RAG non observable, LearnerAgent incomplet — peut être résolu en Sprint 3 avec une prioritisation claire. La bonne nouvelle est que ces problèmes sont tous **identifiés, documentés, et adressables** — ce qui est lui-même un signe de maturité d'équipe.

**Sprint 3 est exécutable, mais doit commencer par les P0 et P1, pas par les nouvelles fonctionnalités (workflow sémantique, standards metadata) qui sont prévues à tort comme prioritaires dans la roadmap actuelle.**

---

*Rapport généré par analyse des logs de production, du code source, et des documents d'audit existants.*
*Sources : error.md (logs 22-23 Fév 2026), OPERATIONAL_REALITY.md, Roadmap2.0.md (v1.5), code source factory-sprint0/*
