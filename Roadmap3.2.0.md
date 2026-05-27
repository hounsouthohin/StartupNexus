# ROADMAP — SOFTWARE AGENT FACTORY
## Version 3.2 — Mise à jour 24 Mai 2026
## Historique : v2.0 (23 Fév) · v2.1 (03 Mars) · v2.2 (04 Mars) · v2.3 (28 Mars) · v3.0 (09 Mai) · v3.1 (15 Mai) · v3.2 (24 Mai — Vision agentic startup affirmée, expansion déterministe par type, déploiement Vercel+Neon, innovations A–H intégrées)

---

## VISION (v3.2 — affinée)

**Une startup agentique** : un seul opérateur humain recueille les briefs clients,
les valide et les soumet à la factory. La factory génère, teste et déploie l'application
complète — Next.js 14 + Clerk + Prisma — prête à être consommée par l'utilisateur final.
Aucun développeur. Aucune intervention manuelle entre la commande et le déploiement.

Le moteur repose sur un **modèle compilateur** :
```
Brief (langage naturel)
  → Architect LLM  →  ProjectSpec (IR formel)
  → Générateurs déterministes  →  Squelette garanti
  → Executor LLM (Level B)    →  Logique custom bornée
  → Build + Tests + Reviewer  →  Gate qualité
  → GitHub + Vercel + Neon    →  App déployée, URL livrée
```

La valeur différenciante : les **garanties déterministes** sur la couche données
(services, types, schémas, actions, formulaires, navigation) rendent la factory
structurellement plus fiable que tout outil de génération LLM pur.

Chaque run améliore la factory : les erreurs détectées alimentent les standards Qdrant
via le Learner. L'usine apprend de chaque app qu'elle produit.

---

## PRINCIPES ARCHITECTURAUX (v3.2 — 7 principes)

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
Les fixes gardes-fous masquent l'apprentissage → corriger à la source.

**PRINCIPE 4 — Déterministe pour la forme, Agentique pour le sens**
Les compilateurs (tsc, prisma, next build) sont les arbitres de compilabilité.
Les agents LLM sont les arbitres de sémantique (IDOR, conformité brief, cohérence).
Les deux niveaux coexistent — le déterministe ne disparaît pas, il se concentre.

**PRINCIPE 5 — L'agent reviewer s'auto-rend inutile**
Chaque pattern détecté par le reviewer devient un standard Qdrant (via Learner).
Le Dev apprend → le reviewer corrige moins → les standards s'enrichissent.
Un reviewer qui ne détecte plus rien = succès, pas inutilité.

**PRINCIPE 6 — Complétion avant complexité**
Un niveau doit être fonctionnellement complet avant d'introduire le niveau suivant.
Le Level A (CRUD SaaS simple) doit être prouvé utilisable par un vrai utilisateur
avant de passer au type suivant.
Construire du multi-tenant sur des formulaires cassés = construire sur du sable.

**PRINCIPE 7 — Extension avant limitation** *(ajouté v3.2)*
Quand la factory ne sait pas générer un type d'app, la réponse est d'étendre la couche
déterministe (nouveaux générateurs, nouveaux standards, nouveaux templates),
pas de signaler l'échec au client.
Tout type d'application complexe a une colonne vertébrale déterministe identifiable.
L'objectif est de l'encoder — pas de contourner.

---

## ÉTAT ACTUEL — 24 Mai 2026 (Niveau 1 stable, Niveau 2 en cours)

### Acquis confirmés

**Pipeline Temporal complet :**
`architect_activity → dev_test_activity → review_activity → qa_activity → learner_activity`
*(github_activity en PAUSE volontaire — condition de réactivation : Sprint 5D)*

**Build stable :** Type A validé sur project-hub, contact-crm, leave-manager, invoice-tracker.
Type D (personal-blog) : build_success=true mais fonctionnalité utilisateur incomplète.

**Architecture modules :**
- `agents/core/` : pipeline_types, error_parser, requirements_engine, spec_coverage,
  journey_validator, quality_validator (stack-agnostiques)
- `agents/stacks/` : StackAdapter pattern
- Level A complet : services, actions, types, schémas, middleware, form generator (Jinja2), pages

**RAG actif :** 116 standards Qdrant, format RULE:/WHY:/GOOD:/BAD:

**Déploiement cible :** Vercel (Next.js) + Neon PostgreSQL (serverless, connection pooling natif Prisma)

---

## SPRINTS COMPLÉTÉS — RÉSUMÉ

| Sprint | Période | Livrables clés |
|--------|---------|----------------|
| 0–3 | Fév–Mars 2026 | Pipeline end-to-end, Stack-as-Config, RAG, Learner shadow mode |
| 4 | Mars–Avr 2026 | Requirements déterministes, contracts v2, Blueprint Validator, spec_coverage |
| 4.5 | Avr 2026 | user_flows[], Journey Validator, seuil is_useful_app |
| Pré-4.6 | Mars 2026 | Refacto Architecture Simplifiée (supervisors LLM inline supprimés) |
| 4.6 | ❌ Abandonné | LLM inline : angles morts partagés → Reviewer post-build |
| T2–T5 | Mai 2026 | agents/core/ extraits, StackAdapter, Docker npm_cache, forbidden_keywords |

---

## SPRINT 4.7 — Complétion Fonctionnelle Level A
## Deadline : Mai–Juin 2026 | STATUT : EN COURS

### Contexte

Test personal-blog révèle : build_success ≠ app utilisable.
Ce sprint clôt la dette fonctionnelle avant toute nouvelle complexité.

### 4.7A — Corrections infrastructure

| Fix | Fichier cible | Impact |
|-----|--------------|--------|
| A1 | `templates/env.local.template` | DIRECT_DATABASE_URL + 4 vars Clerk redirect |
| A2 | `templates/prisma_config.ts` | DIRECT_DATABASE_URL pour migrations Neon/PgBouncer |
| A3 | `templates/env.example.template` + JSON config | .env.example dans chaque projet livré |
| B1 | `dev_navigation_generator.py` + layout template | Navigation depuis spec.pages[] |
| C1 | `dev_service_generator.py` | Supprimer `as unknown as Model[]` + `as any` |
| D1 | `agents/core/journey_validator.py` | Détecter actions.ts par contenu modèle |

### 4.7B — Form Generator déterministe *(Pilier 1 — Jinja2)*

`dev_form_generator.py` — génère `page-client.tsx` pour chaque modèle.

| Type de champ | Rendu HTML |
|---------------|-----------|
| String | `<input type="text">` |
| Int / Float | `<input type="number">` |
| DateTime | `<input type="datetime-local">` |
| Boolean | `<input type="checkbox">` |
| FK (`@relation`) | `<select>` chargé depuis `relatedService.getAll(userId)` |
| Enum / status | `<select>` avec options extraites du spec |

Tous les outputs ajoutés à `template_written` → protégés contre réécriture LLM.

### 4.7C — Extension dev_pages_generator : pages list / detail / edit complètes

- Page `list` : tableau colonnes scalaires + boutons Edit/Delete
- Page `detail` : champs avec labels lisibles
- Page `edit` : form generator en mode édition (valeurs pré-remplies)

### 4.7D — Failles techniques prioritaires (issues audit Mai 2026)

| # | Faille | Priorité | Action |
|---|--------|----------|--------|
| F1 | Progressive Validation absent du graphe | CRITIQUE | Valider chaque write_file via `tsc --noEmit --isolatedModules` |
| F3 | `quality_validator.py` appel bloquant dans async | ÉLEVÉE | Wrapper `asyncio.to_thread()` |
| F4 | `quality_validator.py` fichier zombie si crash | ÉLEVÉE | Context manager `tempfile` dans project_dir |
| F5 | `getAllByUser` absent de `service_map_str` | ÉLEVÉE | CONTRACT.md (voir suggestion G) |
| F6 | Feature modules par side-effect import | MOYENNE | Registre JSON déclaratif (voir suggestion F) |
| F8 | Pagination hardcodée `take:50/20` dans `getPublished`/`getPublicAll` | MOYENNE | Aligner sur pattern `getAll` (page + pageSize) |
| F9 | `update`/`create` retournent `Promise<ModelName>` | MOYENNE | Typer correctement ou documenter |
| F10 | Decimal non sérialisé dans `_serialize` | BASSE | Ajouter Decimal → number dans `_dt_inline_map` |

### 4.7E — Innovations intégrées dans ce sprint

**F. Feature Module Registry déclaratif**
`"feature_modules": ["search", "status_flow"]` dans `nextjs-clerk-prisma.json`.
`run_feature_modules()` charge dynamiquement depuis le JSON. Fin des imports side-effect fragiles.

**G. LevelAManifest étendu + CONTRACT.md généré**
Étendre `LevelAManifest` avec toutes les méthodes de service (signatures exactes).
Générer `CONTRACTS.md` dans le projet → injecté au début de la phase executor.
Le LLM connaît `getAllByUser`, `getBySlug`, etc. sans deviner.

### Signal clôture Sprint 4.7

- `npm install && npm run dev` sans intervention sur un projet extrait
- Utilisateur peut créer/lire/modifier/supprimer sans taper un UUID
- Navigation présente dans le header
- `user_flows_coverage ≥ 0.8` sur un brief Type A standard
- `is_useful_app: true` sur ≥3 runs consécutifs Type A

---

## SPRINT 4.8 — Signal Qualité Réel + QA Agent
## Deadline : Juin 2026 | STATUT : Planifié

### 4.8A — Semantic Reviewer (revivre correction_pass)

Remplacer `reviewer_activity` (retourne toujours 100) par un reviewer structuré.

**Checklist sémantique générée :**
```json
{
  "routes_complete": true,
  "auth_guards_present": false,
  "crud_fields_match_spec": true,
  "no_hardcoded_ids": true,
  "idor_free": false
}
```

**Checks critiques ajoutés :**
- **IDOR** : `userId` présent dans chaque `update`/`delete` service ?
- **Ownership leak** : `getAll()` filtre par `userId` ?
- **Brief conformity** : chaque modèle de `requirements[]` a un service + page list + page create ?
- **Dead server actions** : actions créées mais jamais référencées dans une page ?

**Activation de correction_pass :**
Déclenchée si checklist contient ≥1 `false` → injecte les assertions exactes dans le LLM.
Plus de scoring flou — des cibles précises.

**Format ReviewReport enrichi :**
```json
{
  "coherence_score": 85, "security_score": 70,
  "findings": [{
    "file": "lib/services/post.service.ts",
    "issue_type": "IDOR", "severity": "critical",
    "evidence": "prisma.post.update({ where: { id } }) — userId absent",
    "suggestion": "Ajouter userId dans where : { id, userId }"
  }],
  "verdict": "REVIEW_WITH_FINDINGS"
}
```

### 4.8B — QA Agent réparé

- Fix parsing output LLM (blocs ```typescript si JSON échoue)
- Forcer output JSON schema `{filepath: content}` dans le prompt QA
- Calibration sur 5 runs
- Signal cible : `tests_passed: true` sur ≥1 run

### 4.8C — Findings reviewer → Learner (boucle fermée)

```
Finding IDOR détecté
  → Learner génère StandardSuggestion ZONE_SEC
  → approve_suggestion.py → upsert Qdrant
  → standard injecté dans RAG du prochain run
  → le Dev ne reproduit plus le pattern IDOR
```

### 4.8D — Innovations intégrées dans ce sprint

**E. Semantic Reviewer** : c'est le contenu du 4.8A ci-dessus.

**A. Type Safety Chain Validator** (~30 lignes Python)
Valide la chaîne complète : `SerializedXxx` champs → signatures méthodes service
→ params `actions.ts` → props `page-client`. Rupture détectée avant le build.
Parcourir `model_contexts`, croiser avec `LevelAManifest`, vérifier cohérence des types.

**B. App Usefulness Scorer** (métrique composite)
```
score = build_success (40%) + user_flows_coverage (30%)
      + quality_violations_score (20%) + spec_coverage (10%)
→ is_production_ready: bool + score/100 dans metadata
```
KPI de sortie du pipeline. Remplace l'interprétation fragmentée des métriques isolées.

**H. Learner-Driven Standard Evolution**
Quand `quality_validator` détecte une violation Z24/Z25/Z26, logger le pattern.
Learner déduplique → propose mise à jour standard Qdrant → `approve_suggestion.py`.
Ferme la boucle : violation → standard renforcé → LLM ne répète plus l'erreur.

### Signal clôture Sprint 4.8

- `review_activity` retourne `findings` non-vides sur ≥1 run avec défaut réel
- ≥1 finding IDOR détecté et transmis au Learner
- `tests_passed: true` sur ≥1 run
- Type Safety Chain Validator : 0 faux positifs sur 3 runs Type A

---

## SPRINT 4.9 — Production Readiness Layer
## Deadline : Juillet 2026 | STATUT : Planifié

### Contexte

Un app qui build est une chose. Une app prête pour de vrais utilisateurs en est une autre.
Ce sprint encode de façon déterministe tout ce qu'une app de production requiert.

### 4.9A — dev_production_generator.py (nouveau générateur)

Génère pour chaque projet :

| Fichier | Contenu | Notes |
|---------|---------|-------|
| `vercel.json` | `{"framework": "nextjs"}` | Zero-config Vercel |
| `.env.production.local` | DATABASE_URL Neon + vars Clerk prod | Séparé de .env.local dev |
| `migrate.sh` | `npx prisma migrate deploy` | Pas `db push` en prod |
| `lib/logger.ts` | Logger structuré stdout JSON | Pour plateformes cloud |
| `app/error.tsx` | Error boundary global Next.js | App crashe proprement |
| `app/[route]/error.tsx` | Error boundaries par route | Isolation des erreurs |

**Index Prisma déterministes** (encodés dans `dev_service_generator.py`) :
- `@@index` sur toutes les FK de chaque modèle
- `@@index` sur les champs filtrés fréquemment (status, userId, createdAt)

**Rate limiting** : middleware.ts étendu avec rate limit par IP (via upstash/ratelimit
ou équivalent edge-compatible avec Vercel).

### 4.9B — Innovations intégrées dans ce sprint

**C. Progressive Validation dans dev_graph**
Après chaque `write_file()` par le LLM, valider ce fichier via `tsc --noEmit --isolatedModules`.
Erreur immédiate → message LLM ciblé sur CE fichier uniquement.
Le LLM n'écrit plus 12 fichiers avant de découvrir les erreurs en cascade.

**D. Smart Context Injection par rôle de fichier**
Le `executor_node` connaît le fichier en cours (Plan-and-Execute).
Injecter uniquement les standards pertinents au rôle :
- `actions.ts` → Z26 ($transaction) + auth guard standard
- `service.ts` → Z24 (N+1) + Z25 (select minimal)
- `page-client.tsx` → patterns hooks + loading states
Réduit le bruit dans le contexte LLM, renforce les standards critiques.

**prebuild_pipeline.py — intégration dans dev_graph**
Le `prebuild_pipeline` devient un module de stages appelé par `dev_graph`,
pas un pipeline autonome (évite deux orchestrateurs désynchronisés) :
```
dev_graph.py
  └── pre_generation (déterministe)
  └── executor_node (LLM)
  └── [NEW] post_generation_stage → stages quality_rules + semantic_checks
  └── build_node
  └── extract_build_error_node
```

### Signal clôture Sprint 4.9

- App générée : `npm run build` puis déployable sur Vercel sans modification manuelle
- Index Prisma présents sur ≥3 FK par modèle dans schema.prisma
- `lib/logger.ts` présent dans chaque projet
- Error boundaries présents pour chaque route principale
- Progressive Validation : erreur détectée sur le bon fichier dans les logs

---

## SPRINT 5 — Mode Replay + Type D Blog/CMS
## Deadline : Juillet–Août 2026 | STATUT : Planifié

### Note : GitHub agent

Condition de réactivation : Level A stable sur ≥10 runs consécutifs.
Repo dédié : `factory-generated-apps`. Chaque projet → branche isolée → PR avec run_report.

### 5A — Mode Replay (debugging radical)

Comparer run N (échoué) vs run N-1 (réussi) :
- Fichiers générés (diff ligne à ligne)
- Standards RAG récupérés (IDs Qdrant)
- Décisions LLM (file_plan, patches)
Prérequis déjà en place : run_id propagé, rag_usage.jsonl avec IDs réels.

### 5B — Standards Maintenance Agent (Web Search → Standard)

Quand Learner détecte pattern récurrent (N ≥ 3) :
1. Web search sur ALLOWLIST : `nextjs.org | clerk.com | prisma.io | jestjs.io`
2. LLM génère standard prescriptif (RULE:/WHY:/GOOD:/BAD:)
3. Mode Replay valide que le standard corrige le run défaillant
4. `learner_suggestions.json` → validation humaine → Qdrant

### 5C — Compatibility Matrix dynamique

```json
{"next": "14.2.25", "clerk": "6.x", "prisma": "7.x"} → "validated"
{"next": "15.x",    "clerk": "6.x", "prisma": "7.x"} → "experimental"
```
Critère promotion : 2 runs build_success=true.

### 5D — Expansion Type D : Blog / CMS

**Nouveaux générateurs déterministes :**

| Générateur | Contenu |
|-----------|---------|
| `dev_seo_generator.py` | `<meta>` tags, `og:image`, `sitemap.xml` par modèle publishable |
| Template `rich_textarea.tsx.j2` | Textarea enrichi pour champ `content` |

**Nouveaux standards Qdrant (~6) :**
- SEO metadata pattern (title, description, og)
- Content field handling (textarea vs input)
- Category/tag via junction table
- Draft/publish lifecycle
- Slug-based routing (has_slug déjà dans ModelGenerationContext)
- getPublished() — pagination correcte (fix F8 déjà en 4.7D)

**Signal architect pour Type D :**
Reconnaître "blog", "article", "post", "publication" dans le brief →
activer `has_slug: true` + champ `status` (draft/published) sur les modèles concernés.

**Signal clôture Sprint 5 :**
- Mode Replay opérationnel sur 1 run régressif réel
- ≥1 standard créé depuis web search + validé + Qdrant
- Type D : `is_useful_app: true` sur personal-blog re-run post-générateurs

---

## SPRINT 6 — Type G Booking + GitHub agent
## Deadline : Août–Septembre 2026 | STATUT : Planifié

### Condition d'entrée (PRINCIPE 6)
- Type A : `is_useful_app: true` sur ≥5 runs consécutifs
- Type D : `is_useful_app: true` sur ≥2 runs
- review_activity : findings cohérents (Sprint 4.8 validé)

### 6A — Expansion Type G : Booking / Réservation

**Nouveaux générateurs déterministes :**

| Générateur | Contenu |
|-----------|---------|
| `dev_booking_generator.py` | Slot model (startTime/endTime/isAvailable), queries de conflit, booking FSM (pending→confirmed→cancelled→completed) |
| Template `calendar_picker.tsx.j2` | Date/time picker composant |
| Feature module `"booking_calendar"` | Activé via registre JSON (suggestion F) |

**Nouveaux standards Qdrant (~10) :**
- Détection de conflit de créneaux (findMany where overlap)
- État machine booking (transitions valides uniquement)
- Timezone handling (UTC en DB, locale en UI)
- Politique d'annulation
- Disponibilités récurrentes

**Signal architect pour Type G :**
Reconnaître "réservation", "créneau", "disponibilité", "booking", "rendez-vous" →
activer `booking_calendar` module + modèles Slot + Booking dans le spec.

### 6B — GitHub agent (réactivation)

- Repo `factory-generated-apps` créé
- `github_activity` réactivée conditionnellement
- Chaque projet → branche isolée → PR avec run_report en description

### Signal clôture Sprint 6

- Type G : `is_useful_app: true` sur ≥2 runs booking brief
- Conflit de créneaux détecté déterministiquement (0 double-réservation en test)
- GitHub agent : PR créée avec run_report attaché

---

## SPRINT 7 — Type I Workflow/Approval + Level B Fondations
## Deadline : Septembre–Octobre 2026 | STATUT : Planifié

### Condition d'entrée (PRINCIPE 6)
- Types A, D, G : tous à `is_useful_app: true` sur ≥2 runs consécutifs

### 7A — Expansion Type I : Workflow / Approbation

**Nouveaux générateurs déterministes :**

| Générateur | Contenu |
|-----------|---------|
| `dev_fsm_generator.py` | État machine configurable depuis spec (transitions: pending→approved→rejected), validation des transitions légales uniquement |
| Template `notification_model.prisma.j2` | Modèle Notification structurel si workflow détecté |
| Feature module `"approval_workflow"` | Activé via registre JSON |

**Nouveaux standards Qdrant (~8) :**
- FSM pattern (transitions valides, état intermédiaire interdit)
- Notification triggers (sur changement d'état)
- Audit trail (log de chaque transition avec userId + timestamp)
- Parallel approvals (plusieurs approbateurs)

**Signal architect pour Type I :**
Reconnaître "approbation", "validation", "workflow", "demande", "soumission" →
activer `approval_workflow` module + champ status FSM sur les modèles concernés.

### 7B — Level B Fondations (multi-tenant)

Préparation architecturale sans full implementation :

```python
# ProjectSpec étendu
organizations: bool = False
roles: list[str] = []
```

`dev_membership_generator.py` :
- `lib/services/membership.service.ts` : joinOrg, leaveOrg, getMembers, checkRole
- `lib/permissions.ts` : isOwner(), isAdmin(), requireRole()
- Injection automatique `orgId` sur chaque entité

Nouvelle stack config : `nextjs-clerk-orgs-prisma` (étend nextjs-clerk-prisma).

### Signal clôture Sprint 7

- Type I : `is_useful_app: true` sur ≥1 run approval workflow
- Membership table + orgId dans schema.prisma sur brief multi-tenant test
- `permissions.ts` avec `requireRole()` généré

---

## SPRINT 8 — Level B Multi-tenant Complet + RBAC
## Deadline : Octobre 2026 | STATUT : Planifié

### 8A — Stack `nextjs-clerk-orgs-prisma` complète

```
agents/stacks/nextjs_clerk_orgs_prisma/
  adapter.py
  architect_enhancer.py  ← inject_org_relations()
  dev_graph.py           ← extends nextjs-clerk-prisma + membership generator
config/stacks/nextjs-clerk-orgs-prisma.json
```

### 8B — RBAC Guards dans les templates

`middleware.ts` étendu pour routing par rôle Clerk.
Templates `requires_role.tsx.j2` pour pages protégées par rôle.

### 8C — Dashboard Gouvernance (interface web)

- Voir/modifier `config/stacks/*.json`
- Voir standards Qdrant par stack
- Métriques reviewer par run
- Créer nouvelle stack via formulaire

### Signal clôture Sprint 8

- ≥1 run Notion/Slack clone (workspaces + members) avec `is_useful_app: true`
- RBAC : page admin accessible aux ADMIN uniquement (vérifié par reviewer)
- Dashboard Gouvernance : http://localhost:3001

---

## SPRINT 9 — Stripe + Type E/H + Stack Versioning
## Deadline : Novembre 2026 | STATUT : Planifié

### 9A — Type E (E-commerce) — Stripe Billing

`dev_billing_generator.py` → subscription flow + webhook Stripe.
`dev_cart_generator.py` → cart model, order state machine, checkout flow.

### 9B — Type H (Dashboard Analytics)

`dev_dashboard_generator.py` → aggregation queries (groupBy, count, sum) + chart data endpoints.

### 9C — Stack Versioning

```
nextjs-clerk-prisma@1.0 → next@14.2.25 (stable)
nextjs-clerk-prisma@2.0 → next@15.x   (experimental)
```
Compatibility Matrix (Sprint 5) pilote les promotions.
`.factory-meta.json` par projet généré.

### Signal clôture Sprint 9

- ≥1 run e-commerce brief avec Stripe checkout `is_useful_app: true`
- ≥1 run analytics dashboard avec aggregation queries correctes
- Stack versioning actif sur 2 combinaisons

---

## SPRINT 10 — Level C Marketplace + Stack 2 + Production Ready
## Deadline : Décembre 2026 | STATUT : Planifié

### 10A — Type C Marketplace (nécessite Sprint 8 + 9)

Stack `nextjs-marketplace-prisma` :
Two-actor spec (BUYER/SELLER), Listing/Order/Review models déterministes.
`actors: ["BUYER", "SELLER"]` → pages /buyer/dashboard, /seller/dashboard auto-générées.

### 10B — Stack 2 : `vue-fastapi-sqlalchemy`

Premier test de généralisation du moteur via StackAdapter sur un stack non-Next.js.

### 10C — Playwright E2E sur apps déployées

Tests end-to-end sur l'URL Vercel générée — pas juste `npm run build`.
Signal final : l'utilisateur peut réaliser tous ses `user_flows` sur l'app déployée.

### 10D — Démo 50 projets

- 20 projets Type A, 10 Type D, 10 Type G, 5 Type I, 5 Type B
- Tous déployés sur Vercel + Neon
- `is_production_ready: true` sur ≥80%

---

## EXPANSION DÉTERMINISTE PAR TYPE D'APP

*Chaque type est débloqué en ajoutant les générateurs et standards listés.
Le LLM (Level B) n'est jamais la réponse à un manque déterministe — on l'encode.*

| Type | Nom | Generators manquants | Standards requis | Signal architect | Sprint cible |
|------|-----|---------------------|-----------------|-----------------|-------------|
| **A** | CRUD SaaS | ✅ Complet | ✅ 116 actifs | — | ✅ 4.7 |
| **D** | Blog/CMS | `dev_seo_generator.py`, `rich_textarea.j2` | ~6 (SEO, content, draft/publish) | "blog", "article", "post" | 5 |
| **G** | Booking | `dev_booking_generator.py`, `calendar_picker.j2` | ~10 (slots, FSM, timezone) | "réservation", "créneau" | 6 |
| **I** | Workflow | `dev_fsm_generator.py`, `notification_model.j2` | ~8 (FSM, audit trail, parallel) | "approbation", "workflow" | 7 |
| **B** | Multi-tenant | `dev_membership_generator.py`, stack `nextjs-clerk-orgs` | ~12 (tenant isolation, RBAC) | "organisation", "workspace" | 7–8 |
| **H** | Dashboard | `dev_dashboard_generator.py` (aggregation queries) | ~6 (groupBy, chart endpoints) | "analytique", "dashboard" | 9 |
| **E** | E-commerce | `dev_billing_generator.py`, `dev_cart_generator.py` | ~15 (Stripe, checkout, inventory) | "boutique", "paiement" | 9 |
| **F** | Social | many-to-many complet, real-time module | ~10 (follows, feeds, notifications) | "réseau", "posts", "like" | 10+ |
| **C** | Marketplace | nécessite B + E, two-actor spec | ~20 (escrow, listing lifecycle) | "acheteur", "vendeur" | 10 |
| **J** | File Mgmt | `dev_storage_generator.py` (S3/R2 integration) | ~8 (upload, permissions, versions) | "fichier", "document", "upload" | 10+ |

**Règle d'expansion (PRINCIPE 7 en pratique) :**
```
Nouveau type détecté dans brief
  → Identifier la partie répétitive (modèles, relations, state machines)
  → Encoder dans un nouveau generator
  → Écrire les standards Qdrant manquants
  → Enseigner les signaux à l'architect
  → Le LLM garde uniquement la logique vraiment custom
```

---

## DÉPLOIEMENT — Architecture Standard

### Stack déploiement pour apps générées

```
App générée
  → github_activity push → repo factory-generated-apps (branche par projet)
  → Vercel (auto-deploy depuis GitHub, zero-config Next.js 14)
  → Neon PostgreSQL (serverless, connection pooling Prisma intégré)
  → Clerk (auth, déjà dans le stack)

Coût par projet client :
  Phase MVP    : ~0€ (free tiers Vercel + Neon)
  Phase prod   : ~20–30€/mois (Vercel Pro + Neon Launch)
  Phase scale  : ~50–100€/mois selon trafic
```

### Pourquoi Neon et pas Supabase/PlanetScale

Neon = serverless PostgreSQL avec connection pooling natif compatible Prisma.
Vercel + Prisma sans connection pooler = saturation de connexions en serverless.
Supabase fonctionne aussi mais ajoute des features non utilisées (Storage, Realtime).
PlanetScale a supprimé son free tier.

### Ce que `dev_production_generator.py` génère (Sprint 4.9)

```
vercel.json                  ← {"framework": "nextjs"}
.env.production.local        ← DATABASE_URL (Neon) + Clerk prod vars
migrate.sh                   ← npx prisma migrate deploy (pas db push)
lib/logger.ts                ← Logger structuré stdout JSON
app/error.tsx                ← Error boundary global
app/[route]/error.tsx        ← Error boundaries par route
schema.prisma (enrichi)      ← @@index sur FK + champs filtrés fréquemment
```

### Pipeline de livraison client (post Sprint 4.9)

```
1. Brief client reçu et validé par l'opérateur
2. Run factory → app générée (8–15 min)
3. github_activity → push branche
4. Vercel deploy automatique → URL preview
5. Vérification is_useful_app: true + score/100
6. URL livrée au client
```

---

## INNOVATIONS ARCHITECTURALES — Catalogue A→H

*(Référence technique — chaque lettre = un artefact à implémenter dans le sprint indiqué)*

| # | Nom | Sprint | Description courte |
|---|-----|--------|-------------------|
| A | Type Safety Chain Validator | 4.8D | Valide SerializedXxx → service → actions → page-client avant build |
| B | App Usefulness Scorer | 4.8D | Score composite : build(40%) + flows(30%) + quality(20%) + spec(10%) |
| C | Progressive Validation | 4.9B | `tsc --noEmit --isolatedModules` après chaque write_file() LLM |
| D | Smart Context Injection | 4.9B | Standards pertinents uniquement selon le rôle du fichier en cours |
| E | Semantic Reviewer | 4.8A | Checklist vrai/faux → targets précises pour correction_pass |
| F | Feature Module Registry | 4.7E | Registre JSON déclaratif → fin des side-effect imports |
| G | LevelAManifest + CONTRACT.md | 4.7E | Toutes les méthodes service exposées → LLM ne devine plus |
| H | Learner-Driven Standards | 4.8D | Violations quality_validator → Learner → standards Qdrant |

---

## JALONS v3.2

| Date cible | Sprint | Livrable clé | Signal mesurable | Statut |
|------------|--------|-------------|-----------------|--------|
| Mars 2026 | 0–3 | Pipeline end-to-end | build_success reproductible | ✅ |
| Avril 2026 | 4 | Gate décisionnel + contracts v2 | spec_coverage + requirements | ✅ |
| Avril 2026 | 4.5 | Journey Validator | user_flows_covered 100% Type A | ✅ |
| Mai 2026 | T2–T5 | agents/core/ + StackAdapter + Docker | Refacto sans régression | ✅ |
| Mai–Juin 2026 | **4.7** | Form Generator + Pages complètes + F→G innovations | `is_useful_app: true` ≥3 runs A | ⏳ |
| Juin 2026 | **4.8** | Semantic Reviewer + QA réparé + A/B/H innovations | findings non-vides + `tests_passed` | ⏳ |
| Juillet 2026 | **4.9** | Production Readiness Layer + C/D innovations | App déployable Vercel sans modification | ⏳ |
| Juil–Août 2026 | 5 | Mode Replay + Standards Web + Type D | `is_useful_app: true` personal-blog | ⏳ |
| Août–Sept 2026 | 6 | Type G Booking + GitHub réactivé | `is_useful_app: true` booking brief | ⏳ |
| Sept–Oct 2026 | 7 | Type I Workflow + Level B fondations | `is_useful_app: true` approval brief | ⏳ |
| Octobre 2026 | 8 | Level B complet + RBAC + Dashboard | Notion clone `is_useful_app: true` | ⏳ |
| Novembre 2026 | 9 | Stripe + Type E/H + Stack versioning | E-commerce `is_useful_app: true` | ⏳ |
| Décembre 2026 | 10 | Type C Marketplace + Stack 2 + Démo 50 | 50 projets déployés, 80% score≥70 | ⏳ |

---

## DETTE TECHNIQUE CONNUE

| # | Description | Sprint cible |
|---|-------------|-------------|
| D1 | `(data as any)` dans les services | 4.7A (C1) |
| D2 | IDOR sur update (userId absent du where) | 4.8A |
| D3 | `updatedAt` manquant sur certains modèles | 5 |
| D4 | Pagination hardcodée `take:20` dans `getPublished`/`getPublicAll` | 4.7D (F8) |
| D5 | User model orphelin (no FK vers entités) | Design decision 7 |
| D6 | GitHub agent désactivé | Réactivation conditionnelle 6 |
| D7 | `test_sprint1_validation.py` legacy | Archiver 5 |
| D8 | `learner_agent_contract.json` zombie | Supprimer 5 |
| D9 | `reviewer_activity` score 100 sur apps défectueuses | 4.8A |
| D10 | `journey_validator` sous-compte les flows couverts | 4.7A (D1) |
| D11 | Progressive Validation décrite dans commentaires mais absente du graphe | 4.9B (F1) |
| D12 | `quality_validator.py` : appel bloquant dans async + zombie file | 4.7D (F3/F4) |
| D13 | `getAllByUser` absent de `service_map_str` | 4.7E (G) |
| D14 | Feature modules via side-effect imports | 4.7E (F) |
| D15 | `SpecOutput` contrat zombie (toujours les defaults) | Nettoyer 5 |
| D16 | `update`/`create` retournent `Promise<ModelName>` pas `SerializedXxx` | 4.7D (F9) |
| D17 | Decimal non sérialisé dans `_serialize` | 4.7D (F10) |
| D18 | Enum : union literals au lieu d'imports Prisma | 5 (cosmétique) |
| D19 | `prebuild_pipeline.py` orchestrateur séparé de `dev_graph` | 4.9B (intégration) |

---

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
| Mai 2026 | GitHub agent mis en PAUSE | Éviter création de dizaines de repos pendant la phase test |
| Mai 2026 | Reséquençage : complétion Level A avant Level B | PRINCIPE 6 — test Type D révèle formulaires non fonctionnels |
| Mai 2026 | Form Generator déterministe (Pilier 1) | Les formulaires sont de la donnée structurée |
| **Mai 2026** | **Extension avant limitation (PRINCIPE 7)** | **Tout type d'app a une colonne vertébrale déterministe à encoder** |
| **Mai 2026** | **Déploiement standard : Vercel + Neon PostgreSQL** | **Connection pooling natif Prisma, zero-config Next.js, free tier généreux** |
| **Mai 2026** | **Sprint 4.9 : Production Readiness Layer** | **Gap entre build_success et app production-ready — indexes, logging, error boundaries** |
| **Mai 2026** | **Vision affirmée : agentic startup opérée par un humain unique** | **Opérateur recueille briefs, factory génère + déploie, zero développeur** |
