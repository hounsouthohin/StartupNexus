# ROADMAP — SOFTWARE AGENT FACTORY
## Version 3.1 — Mise à jour 15 Mai 2026
## Historique : v2.0 (23 Fév) · v2.1 (03 Mars) · v2.2 (04 Mars) · v2.3 (28 Mars) · v3.0 (09 Mai) · v3.1 (15 Mai — reséquençage post-test Type D)

---

## VISION (inchangée)

Usine logicielle 100% autonome et auto-apprenante transformant une commande humaine
en application full-stack déployée, testée, sécurisée et constamment améliorée,
sans intervention humaine.

---

## PRINCIPES ARCHITECTURAUX (v3.1 — enrichis)

**PRINCIPE 1 — Le code exécute, la configuration décide**
Toute règle stack-spécifique vit dans `config/stacks/*.json`.
Le code Python est un exécuteur générique.
Ajouter une stack = créer un JSON + un StackAdapter. Zéro Python core modifié.

**PRINCIPE 2 — Standards prescriptifs, pas descriptifs**
Chaque standard Qdrant dit : RULE:/WHY:/GOOD:/BAD:
Un standard sans exemple négatif est incomplet.
Les standards sont la source de connaissance — le code est l'exécuteur.

**PRINCIPE 3 — La boucle d'apprentissage doit être fermée**
RAG → Dev → Build → Reviewer → Learner → RAG
Chaque maillon est implémenté avant de passer au suivant.
Les fixes gardes-fous masquent l'apprentissage → corriger à la source (standards/prompts).

**PRINCIPE 4 — Déterministe pour la forme, Agentique pour le sens**
Les compilateurs (tsc, prisma, next build) sont les arbitres de compilabilité.
Les agents LLM sont les arbitres de sémantique (IDOR, conformité brief, cohérence).
Les deux niveaux coexistent — le déterministe ne disparaît pas, il se concentre.

**PRINCIPE 5 — L'agent reviewer s'auto-rend inutile**
Chaque pattern détecté par le reviewer devient un standard Qdrant (via Learner).
Le Dev apprend → le reviewer corrige moins → les standards s'enrichissent.
Un reviewer qui ne détecte plus rien = succès, pas inutilité.

**PRINCIPE 6 — Complétion avant complexité (ajouté v3.1)**
Un niveau doit être fonctionnellement complet avant d'introduire le niveau suivant.
Le Level A (CRUD SaaS simple) doit être prouvé utilisable par un vrai utilisateur
avant de passer au Level B (multi-tenant).
Construire du multi-tenant sur des formulaires cassés = construire sur du sable.

---

## ÉTAT ACTUEL — 15 Mai 2026 (Niveau 1 atteint, Niveau 2 en cours)

### Acquis confirmés

**Pipeline Temporal complet :**
`architect_activity → dev_test_activity → review_activity → qa_activity → learner_activity`
*(github_activity en PAUSE volontaire — voir section dédiée)*

**Build stable :** Type A validé sur project-hub, contact-crm, leave-manager,
invoice-tracker. Type D (personal-blog) premier test effectué — build_success=true
mais fonctionnalité utilisateur incomplète (formulaires, navigation).

**Architecture modules :**
- `agents/core/` : pipeline_types, error_parser, requirements_engine, spec_coverage,
  journey_validator, quality_validator (stack-agnostiques, réutilisables)
- `agents/stacks/` : StackAdapter pattern
- Option A complète : services, actions, types, schémas, middleware — tous déterministes

**RAG actif :** 116 standards Qdrant, format RULE:/WHY:/GOOD:/BAD:

**Learner :** shadow mode actif, approve_suggestion.py opérationnel.

### Leçon du test Type D (personal-blog — 15 Mai 2026)

Le test a révélé que le build_success ne suffit pas à qualifier une app comme livrable.
L'app compilait (tsc 0 erreurs, build exit 0) mais n'était pas utilisable :
- Pas de navigation entre les pages
- Formulaires avec champs FK en `<input type="text">` (l'utilisateur devait taper des UUIDs)
- Champ status en texte libre au lieu de `<select>` avec options prédéfinies
- Prisma config non fonctionnelle sans DIRECT_DATABASE_URL (Neon/PgBouncer)
- reviewer_activity donnait score 100/100 malgré ces défauts → signal inutile

**Décision architecturale** : étendre l'Option A aux formulaires et aux pages list/detail
avant d'ajouter de la complexité (Level B, billing, RBAC). PRINCIPE 6 appliqué.

---

## SPRINTS COMPLÉTÉS — RÉSUMÉ

### Sprint 0–3 ✅ (Fév–Mars 2026)
Pipeline end-to-end, Stack-as-Config, RAG actif, LearnerActivity shadow mode,
standards prescriptifs, validate_config_consumption.py, qdrant_filter branché.

### Sprint 4 ✅ (Mars–Avril 2026)
Requirements déterministes, contracts inter-agents v2, Blueprint Validator bloquant,
spec_coverage, anti-patterns auto (Learner P006), approve_suggestion.py,
Qdrant Governance v1 (status=active), Gate Décisionnel.

### Sprint 4.5 ✅ (Avril 2026)
user_flows[] extrait par Architect, Journey Validator opérationnel,
seuil valeur client (spec_coverage > 80% ET user_flows_covered > 60%).

### Pré-Sprint 4.6 ✅ ABSORBÉ (Mars 2026)
Refactorisation Architecture Simplifiée : LLM supervisors inline supprimés,
supervision déterministe uniquement (tsc + build + quality_check.mjs).

### Sprint 4.6 ❌ ABANDONNÉ — Décision définitive
Agents LLM inline supprimés (même modèle générant et reviewant = angles morts partagés).
Remplacement : reviewer post-build avec scope clos (Sprint 4.8).

### Refactorisation T2-T5 ✅ (Mai 2026)
T2 : agents/core/ extraits. T3 : StackAdapter. T4 : Docker npm_cache (~7s).
T5 : forbidden_keywords. architect_enhancer.py extrait.

---

## SPRINT 4.7 — Complétion Fonctionnelle Level A
## Deadline : Mai–Juin 2026 | STATUT : EN COURS

### Contexte et motivation

Le test personal-blog a prouvé que build_success ≠ app utilisable.
Ce sprint règle la dette fonctionnelle avant tout ajout de complexité.

### 4.7A — Corrections infrastructure (6 fixes validés)

Issues révélées par le test. Corrections immédiates, risque zéro.

| Fix | Fichier cible | Impact |
|-----|--------------|--------|
| A1 | `templates/env.local.template` | Ajouter DIRECT_DATABASE_URL + 4 vars Clerk redirect |
| A2 | `templates/prisma_config.ts` | Utiliser DIRECT_DATABASE_URL pour migrations Neon/PgBouncer |
| A3 | Nouveau `templates/env.example.template` + JSON config | .env.example dans chaque projet livré |
| B1 | Nouveau `dev_navigation_generator.py` + layout template | Navigation entre pages depuis spec.pages[] |
| C1 | `dev_service_generator.py` | Supprimer `as unknown as Model[]` (retirer select) + `as any` sur data |
| D1 | `agents/core/journey_validator.py` | Détecter actions.ts par contenu modèle (pas juste par segment URL) |

### 4.7B — Pilier 1 : Form Generator déterministe

**Principe :** Un formulaire est de la donnée structurée. Les champs, types, contraintes
et relations sont dans la spec. Le LLM ne doit pas décider comment afficher un champ FK.

`agents/stacks/nextjs_clerk_prisma/dev_form_generator.py`

**Génère pour chaque modèle :**
- `app/{page}/page-form.tsx` — Client Component avec formulaire complet

**Logique de génération par type de champ :**
| Type de champ | Élément HTML généré |
|---------------|---------------------|
| String | `<input type="text">` |
| Int / Float | `<input type="number">` |
| DateTime | `<input type="datetime-local">` |
| Boolean | `<input type="checkbox">` |
| Champ FK (`@relation`) | `<select>` chargé depuis `relatedService.getAll(userId)` |
| Champ enum / status | `<select>` avec options extraites des contraintes spec |

**Fichiers produits :** ajoutés à `template_written` → protégés contre réécriture LLM.
**Wiring :** appelé dans `dev_graph.py` après `generate_page_stubs`.

### 4.7C — Extension dev_pages_generator : pages list/detail complètes

**Problème :** `dev_pages_generator.py` génère des stubs. Le LLM complète.
Mais une page list suit toujours le même pattern déductible de la spec :
`getAll(userId)` → tableau avec champs scalaires → bouton Edit → bouton Delete.

**Extension :**
- Page `list` : tableau complet avec colonnes depuis `model.fields[]` scalaires,
  boutons Edit (lien vers `/[path]/[id]/edit`) et Delete (appel `deleteXxx` action)
- Page `detail` : affichage de chaque champ avec label lisible (camelCase → espaces)
- Page `edit` : réutilise le form generator (4.7B) en mode édition (valeurs pré-remplies)

**Le LLM garde :** pages custom (dashboard analytique, pages publiques complexes,
logique conditionnelle non déductible de la spec).

### Signal clôture Sprint 4.7

- `npm install && npm run dev` fonctionne sans intervention sur un projet extrait
- Un utilisateur peut créer, lire, modifier, supprimer une entité sans taper un UUID
- Navigation entre toutes les pages présente dans le header
- `user_flows_coverage ≥ 0.8` sur un brief Type A standard
- `is_useful_app: true` sur ≥3 runs consécutifs Type A

---

## SPRINT 4.8 — Signal Qualité Réel + QA Agent
## Deadline : Juin 2026 | STATUT : Planifié

### Contexte

La `review_activity` existe et tourne. Mais elle retourne systématiquement score=100,
findings=[] même sur des apps avec des défauts réels. Le problème n'est pas son absence
— c'est que ses checks sont trop formels (Clerk importé ? Auth guard syntaxiquement présent ?)
et ne reflètent pas la réalité fonctionnelle.

Avec Sprint 4.7 terminé, les formulaires et pages sont déterministes et vérifiables.
La review_activity peut alors se concentrer sur ce que le déterministe ne peut garantir :
la sémantique de sécurité et la conformité métier.

### 4.8A — Renforcer les checks de review_activity

**Checks actuels (trop formaux) :**
- Clerk importé ? → oui/non
- Auth guard syntaxiquement présent ? → oui/non

**Checks ajoutés (sémantiques) :**
- **IDOR** : dans chaque `update` et `delete` service, `userId` est-il dans le `where` ?
  Un `prisma.post.update({ where: { id } })` sans `userId` est une faille réelle.
- **Ownership leak** : `getAll()` filtre-t-il par `userId` ? Sinon, exposition cross-user.
- **Brief conformity** : les modèles listés dans `requirements[]` ont-ils tous
  un service + une page list + une page create générés ?
- **Dead server actions** : les actions `createXxx`/`deleteXxx` sont-elles référencées
  dans au moins une page ? (détection de code généré mais jamais utilisé)

**Format du ReviewReport (enrichi) :**
```json
{
  "coherence_score": 85,
  "security_score": 70,
  "findings": [
    {
      "file": "lib/services/post.service.ts",
      "issue_type": "IDOR",
      "severity": "critical",
      "evidence": "prisma.post.update({ where: { id } }) — userId absent du where",
      "suggestion": "Ajouter userId dans where : { id, userId }"
    }
  ],
  "verdict": "REVIEW_WITH_FINDINGS"
}
```

**Activation progressive (inchangée) :**
- Phase calibration (10 premiers runs) : advisory, tous findings loggés
- Phase production : bloquant sur critical (IDOR, missing auth), advisory sur medium/low

### 4.8B — Réparer QA agent

`tests_passed: false` depuis des sprints. Le pipeline ne tourne pas en entier.
Non bloquant sur le build, mais signal cassé qui fausse l'image de santé du système.

- Fix parsing output LLM (blocs ```typescript si JSON échoue)
- Forcer output JSON schema `{filepath: content}` dans le prompt QA
- Calibrer sur 5 runs — vérifier que les tests générés correspondent aux routes réelles
- Signal cible : `[QA] N tests générés` visible dans les logs sur 3 runs consécutifs

### 4.8C — Findings reviewer → Learner (boucle fermée)

Actuellement le Learner reçoit des suggestions depuis `last_build_error` (P006).
Extension : findings de la review_activity alimentent aussi le Learner.

```
finding IDOR détecté
  → Learner génère StandardSuggestion ZONE_SEC
  → approve_suggestion.py → upsert Qdrant
  → standard injecté dans RAG du prochain run
  → le Dev ne reproduit plus le pattern IDOR
```

### Signal clôture Sprint 4.8

- review_activity retourne `findings` non-vides sur ≥1 run avec défaut réel
- ≥1 finding IDOR détecté et transmis au Learner
- ≥1 StandardSuggestion générée depuis finding reviewer → Qdrant
- QA agent : tests générés sur 3 runs consécutifs
- `tests_passed: true` sur ≥1 run

---

## SPRINT 4.9 — LLM Cost & Token Efficiency
## Deadline : Juin–Juillet 2026 | STATUT : Planifié

### Contexte et motivation

Malgré gpt-4o-mini (modèle le moins cher d'OpenAI), chaque run consomme significativement
de tokens. Root cause analysée en Mai 2026 : le coût vient de la structure du prompt,
pas du modèle. Level A réduit le scope (le LLM génère moins de fichiers) mais pas les tokens
envoyés à chaque tour (system prompt + contexte accumulé restent massifs).

**Leviers identifiés (par ordre d'impact estimé) :**

| # | Levier | Type | Impact estimé |
|---|--------|------|---------------|
| L1 | OpenAI server-side prompt caching (automatique, seed=42) | Infra | ~50% input tokens répétés |
| L2 | LangChain InMemoryCache process-level | Infra | 100% économie sur calls identiques |
| L3 | Compression du contexte : retirer les fichiers confirmés OK | Architecture | 40-60% input tokens par itération |
| L4 | System prompt en deux parties : invariant (cache) + variable (run-specific) | Architecture | 30% input tokens sur system msg |
| L5 | RAG k : 5 → 3 (docs 4-5 ont score <0.45) | Config | ~800 tokens/run |
| L6 | Ne pas injecter `pages_detail` pour toutes les pages d'un coup | Architecture | ~2K tokens/run sur grands projets |

**L1 et L2 déjà implémentés (Mai 2026)** dans `llm_provider.py` (InMemoryCache) et
`dev_graph.py` (seed=42). Ces deux leviers sont à coût d'implémentation nul.

### 4.9A — Mesure de base (prérequis aux autres sprints)

Avant d'implémenter L3-L6, mesurer l'impact réel de L1+L2.

- Ajouter `cached_tokens` dans les run_report : extraire `usage.prompt_tokens_details`
  depuis la réponse OpenAI (via LangChain callback `on_llm_end`)
- Métriques cible par run : `total_input_tokens`, `cached_input_tokens`, `output_tokens`, `estimated_cost_usd`
- Script `scripts/cost_report.py` : agrège les run_reports → coût total par batch

### 4.9B — Compression de contexte entre itérations

Problème : quand le dev agent retry, il reçoit en contexte TOUS les fichiers déjà générés
(même ceux sans erreur). Pour project-hub (3 itérations, 49 fichiers), l'itération 3
contient le contexte complet des itérations 1 et 2.

Solution : dans `_prune_messages()`, après chaque build retry, remplacer les ToolMessages
"fichier écrit" pour les fichiers SANS erreur TSC par un résumé compact :
`"[N fichiers confirmés OK — retirés du contexte pour économiser les tokens]"`

Les seuls fichiers qui restent dans le contexte étendu sont ceux cités dans le build error.

### 4.9C — System prompt split : invariant vs variable

Le system prompt actuel mélange contenu invariant (stack rules, coding standards) et
contenu variable (schema.prisma du projet, pages, spec). OpenAI's prefix caching ne
peut capturer que le préfixe exact. Si le contenu variable est intercalé dans l'invariant,
le cache rate.

Solution : restructurer le system prompt en deux blocs ordonnés :
1. **Bloc INVARIANT** (identique pour tous les projets next-clerk-prisma) — stack rules, patterns, anti-patterns, coding standards. Ce bloc sera mis en cache côté OpenAI.
2. **Bloc VARIABLE** (spécifique au run) — schema.prisma du projet, spec pages, blueprints.

Cela maximise le nombre de tokens capturés par le prompt cache OpenAI.

### 4.9D — RAG k reduction + pages_detail lazy injection

- Réduire k de 5 → 3 dans les CONTEXT_QUERIES (`dev_prompts.py`) pour les queries à faible score (< 0.50)
- `pages_detail` : injecter uniquement le blueprint de la page en cours de génération
  (compatible avec le Track 2 Phase-Aware system prompt)

### Signal clôture Sprint 4.9

- `cost_report.py` : coût par run visible dans les métriques
- `cached_input_tokens > 0` dans au moins 1 run (confirme L1 actif)
- Réduction mesurée ≥ 20% du coût par run vs baseline (après L3 ou L4)

---

## SPRINT 5 — Pipeline Health + Mode Replay + Standards Web
## Deadline : Juillet 2026 | STATUT : Planifié

### Note : GitHub agent en PAUSE

L'agent GitHub est volontairement désactivé pendant la phase de test.
Chaque run crée un projet complet — activer GitHub créerait des dizaines de repos
de test sur le compte, ce qui est contre-productif et difficile à nettoyer.

**Condition de réactivation :** Level A stable sur ≥10 runs consécutifs,
puis activation sur un repo dédié aux projets factory (pas le repo usine).

### 5A — Mode Replay

Outil de debugging radical pour les runs régressifs.

Si run N échoue et run N-1 réussissait, comparer :
- Fichiers générés (diff ligne à ligne) — où la divergence s'est-elle produite ?
- Standards RAG récupérés (IDs Qdrant) — un standard a-t-il changé entre les deux runs ?
- Décisions LLM (file_plan, patches) — quel fichier a divergé en premier ?

Prérequis déjà en place : run_id propagé partout, rag_usage.jsonl avec IDs réels.

### 5B — StandardsMaintenanceAgent (Web Search → Standard)

Quand le Learner détecte un pattern récurrent (N ≥ 3 occurrences) :
1. StandardsMaintenanceAgent cherche sur le web — sources officielles uniquement
   ```
   ALLOWLIST : nextjs.org | clerk.com | prisma.io | jestjs.io
   ```
2. LLM génère standard prescriptif (RULE:/WHY:/GOOD:/BAD:) depuis les résultats
3. Mode Replay valide que le standard corrige le run défaillant
4. Écriture dans learner_suggestions.json → validation humaine → Qdrant

### 5C — Compatibility Matrix dynamique

Remplace VERSION_PINS hardcodés :
```json
{"next": "14.2.25", "clerk": "6.x", "prisma": "7.x"} → "validated"
{"next": "15.x",    "clerk": "6.x", "prisma": "7.x"} → "experimental"
```
Critère promotion : 2 runs build_success=true → "validated"

### 5D — GitHub agent (réactivation conditionnelle)

Réactivé seulement si la condition de Sprint 5 Note est remplie.
Repo dédié : `factory-generated-apps` (pas le repo usine).
Chaque projet → branche isolée → PR avec run_report en description.

### Signal clôture Sprint 5

- Mode Replay opérationnel sur 1 run régressif réel
- ≥1 standard créé depuis web search + validé + Qdrant
- Compatibility Matrix : ≥2 combinaisons évaluées
- GitHub (si réactivé) : PR créée avec run_report attaché

---

## SPRINT 6 — Level B : Multi-tenant Fondations
## Deadline : Août 2026 | STATUT : Planifié

### Condition d'entrée (PRINCIPE 6)

Ce sprint ne démarre que si :
- `is_useful_app: true` sur ≥5 runs Type A consécutifs (Sprint 4.7 validé)
- review_activity retourne des findings cohérents (Sprint 4.8 validé)
- QA agent fonctionnel (Sprint 4.8B validé)

### Contexte

Level A (CRUD SaaS simple) prouvé fonctionnel. Level B = organisations/workspaces.
L'architecture StackAdapter permet d'ajouter Level B sans toucher au moteur.

### 6A — ProjectSpec étendu

```python
organizations: bool = False         # Clerk Orgs — multi-tenant
roles: list[str] = []               # ["OWNER", "ADMIN", "MEMBER"]
billing_provider: str = ""          # "stripe"
actors: list[str] = []              # ["BUYER", "SELLER"] marketplace
```

### 6B — Générateur Membership (déterministe)

`agents/stacks/nextjs_clerk_prisma/dev_membership_generator.py`
- `lib/services/membership.service.ts` : joinOrg, leaveOrg, getMembers, checkRole
- `lib/permissions.ts` : isOwner(), isAdmin(), requireRole()
- Injection automatique de `orgId` sur chaque entité

### 6C — Stack `nextjs-clerk-orgs-prisma`

```
agents/stacks/nextjs_clerk_orgs_prisma/
  adapter.py          ← StackAdapter
  architect_enhancer.py  ← inject_org_relations()
  dev_graph.py        ← extends nextjs-clerk-prisma + membership generator
config/stacks/nextjs-clerk-orgs-prisma.json
```

### Signal clôture Sprint 6

- ≥1 run Notion/Slack clone (workspaces + members) avec build_success=true
- Membership table + orgId dans le schéma Prisma généré
- permissions.ts avec requireRole() généré correctement
- Condition d'entrée Sprint 6 vérifiée avant démarrage

---

## SPRINT 7 — Billing + RBAC + Dashboard Gouvernance
## Deadline : Septembre 2026 | STATUT : Planifié

### 7A — Stripe Billing
`dev_billing_generator.py` → subscription flow + webhook Stripe.

### 7B — RBAC Guards dans les templates
`middleware.ts` étendu pour routing par rôle Clerk.

### 7C — Dashboard Gouvernance (interface web)
- Voir/modifier config/stacks/*.json
- Voir standards Qdrant par stack
- Métriques reviewer par run
- Créer nouvelle stack via formulaire

### 7D — SanitizerRegistry
Sanitizers hardcodés dans shared_tools.py → registry déclarative JSON.

### Signal clôture Sprint 7
- ≥1 run Notion clone (RBAC complet) avec build_success=true
- Stripe subscription flow sur brief avec billing_provider="stripe"
- Dashboard Gouvernance accessible sur http://localhost:3001

---

## SPRINT 8 — Marketplace (Level C) + Stack Versioning
## Deadline : Octobre 2026 | STATUT : Planifié

### 8A — Stack `nextjs-marketplace-prisma`
Two-actor spec (BUYER/SELLER), Listing/Order/Review models déterministes.

### 8B — Brief Two-Actor
`actors: ["BUYER", "SELLER"]` → pages /buyer/dashboard, /seller/dashboard auto-générées.

### 8C — Stack Versioning
```
nextjs-clerk-prisma@1.0 → next@14.2.25 (stable)
nextjs-clerk-prisma@2.0 → next@15.x
```
Compatibility Matrix (Sprint 5) pilote les promotions.

### Signal clôture Sprint 8
- ≥1 run Etsy/Airbnb clone (BUYER/SELLER, listings, orders) avec build_success=true
- Stack versioning : `.factory-meta.json` par projet généré

---

## SPRINT 9 — Production Ready
## Deadline : Novembre 2026 | STATUT : Planifié

- Vercel Preview Deploys depuis github_activity
- Playwright E2E sur apps déployées
- Démo 50 projets autonomes (A + B + C niveaux)
- Stack 2 : `vue-fastapi-sqlalchemy`
- Stack 3 : `nextjs-supabase`

---

## JALONS v3.1

| Date cible | Sprint | Livrable clé | Signal mesurable | Statut |
|------------|--------|-------------|-----------------|--------|
| Mars 2026 | 0–3 | Pipeline end-to-end | build_success reproductible | ✅ |
| Avril 2026 | 4 | Gate décisionnel + contracts v2 | spec_coverage + requirements | ✅ |
| Avril 2026 | 4.5 | Journey Validator | user_flows_covered 100% Type A | ✅ |
| Mai 2026 | T2-T5 | agents/core/ + StackAdapter + Docker | Refacto sans régression | ✅ |
| Mai–Juin 2026 | **4.7** | **6 fixes + Form Generator + Pages complètes** | **is_useful_app: true ≥3 runs** | ⏳ |
| Juin 2026 | **4.8** | **Reviewer checks réels + QA réparé** | **findings non-vides + tests_passed** | ⏳ |
| Juin–Juil 2026 | **4.9** | **LLM Cost Efficiency** | **cached_tokens > 0 + réduction ≥20% coût** | ⏳ (L1+L2 ✅) |
| Juillet 2026 | 5 | Mode Replay + Standards web (GitHub en pause) | 1 standard web validé | ⏳ |
| Août 2026 | 6 | Level B fondation (conditionnel) | 1 multi-tenant build_success | ⏳ |
| Sept 2026 | 7 | Stripe + RBAC + Dashboard | 1 Notion clone complet | ⏳ |
| Oct 2026 | 8 | Level C marketplace | 1 Etsy clone build_success | ⏳ |
| Nov 2026 | 9 | 50 projets A+B+C, deploy Vercel | Démo publique | ⏳ |

---

## DETTE TECHNIQUE CONNUE

| # | Description | Sprint cible |
|---|-------------|-------------|
| D1 | `(data as any)` dans les services | Fix 4.7A (C1) |
| D2 | IDOR sur update (userId absent du where) | Review checks 4.8A |
| D3 | updatedAt manquant sur certains modèles | dev_service_generator Sprint 5 |
| D4 | Pagination hardcodée `take:20` | Standard Qdrant Sprint 5 |
| D5 | User model orphelin (no FK vers entités) | Design decision Sprint 6 |
| D6 | GitHub agent désactivé | Réactivation conditionnelle Sprint 5D |
| D7 | test_sprint1_validation.py legacy | Archiver Sprint 5 |
| D8 | learner_agent_contract.json zombie | Supprimer Sprint 5 |
| D9 | reviewer_activity score 100 sur apps défectueuses | Fix 4.8A |
| D10 | journey_validator sous-compte les flows couverts | Fix 4.7A (D1) |
| D11 | Relations many-to-many non supportées (ex: Post ↔ Tag via table pivot) | Sprint 9+ — nécessite junction table, types Prisma implicites, et UI multi-select |

---



##### Déploiement 




## DÉCISIONS ARCHITECTURALES (log permanent)

| Date | Décision | Raison |
|------|----------|--------|
| Fév 2026 | Stack-as-Config JSON | PRINCIPE 1 — zéro logique stack en Python |
| Mars 2026 | Guards regex → WARN | TypeScript/Prisma sont arbitres |
| Mars 2026 | Sprint 4.6 abandonné | LLM inline supervisors : angles morts partagés |
| Mars 2026 | requirements[] déterministe | Élimine ghost success |
| Avril 2026 | StackAdapter pattern | Multi-stack sans toucher au moteur |
| Avril 2026 | agents/core/ extraction | Stack-agnostique réutilisable |
| Mai 2026 | Reviewer post-build | Scope clos, modèle différent, advisory |
| Mai 2026 | Déterministe ≠ supprimé | Le déterministe se concentre sur la forme |
| **Mai 2026** | **GitHub agent mis en PAUSE** | **Éviter création de dizaines de repos pendant la phase test** |
| **Mai 2026** | **Reséquençage : complétion Level A avant Level B** | **PRINCIPE 6 — test Type D révèle formulaires non fonctionnels** |
| **Mai 2026** | **Form Generator déterministe (Pilier 1)** | **Les formulaires sont de la donnée structurée — ne pas laisser au LLM** |
