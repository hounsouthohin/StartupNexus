# ROADMAP — SOFTWARE AGENT FACTORY
## Version 3.0 — Mise à jour 09 Mai 2026
## Historique : v2.0 (23 Fév) · v2.1 (03 Mars) · v2.2 (04 Mars) · v2.3 (28 Mars) · v3.0 (09 Mai — post-stabilisation)

---

## VISION (inchangée)

Usine logicielle 100% autonome et auto-apprenante transformant une commande humaine
en application full-stack déployée, testée, sécurisée et constamment améliorée,
sans intervention humaine.

---

## PRINCIPES ARCHITECTURAUX (v3.0)

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

---

## ÉTAT ACTUEL — 09 Mai 2026 (Niveau 1 atteint)

### Acquis confirmés

**Pipeline Temporal complet :**
`architect_activity → dev_test_activity → qa_activity → github_activity → learner_activity`

**Build stable :** project-hub — 41 fichiers, build_exit_code=0, TSC 0 erreurs,
0 violations qualité, journey_validator 2/2 (100%), prisma validate OK.

**Architecture modules :**
- `agents/core/` : pipeline_types, error_parser, requirements_engine, spec_coverage,
  journey_validator, quality_validator (stack-agnostiques, réutilisables)
- `agents/stacks/` : StackAdapter pattern — `get_adapter_for_stack(stack_id)` registry
- `agents/stacks/nextjs_clerk_prisma/architect_enhancer.py` : inject_prisma_relations
- Docker T4 : cp node_modules depuis npm_cache (~7s vs ~40s npm install)

**RAG actif :** 116 standards Qdrant (ZONE_1-14, ZONE_17B-30, ZONE_HARD_RULES),
format RULE:/WHY:/GOOD:/BAD:, filtre metadata.status=active opérationnel.

**Learner :** shadow mode actif, génère StandardSuggestion structurées,
approve_suggestion.py opérationnel (workflow y/n → upsert Qdrant ZONE_14).

### Déficits actifs (non bloquants)

| Agent | État | Cause |
|-------|------|-------|
| QA agent | Échoue silencieusement | Parsing JSON output LLM fragile |
| GitHub agent | Échoue silencieusement | GITHUB_TOKEN non injecté dans Docker |
| tests_passed | Non activé | Jest mocks Next.js non configurés |
| Reviewer sémantique | Absent | Prévu Sprint 4.8 |

### Déficits qualité (applicatif généré)

| Défaut | Impact | Correctif cible |
|--------|--------|----------------|
| IDOR sur `update` (no `userId` dans `where`) | Sécurité réelle | Reviewer sémantique → standard Qdrant |
| `(data as any)` dans les services | Type safety | Standard Qdrant existant à renforcer |
| `updatedAt` manquant sur Project/Task/Comment | Modèle incomplet | dev_service_generator.py |
| Pas de gestion d'erreur dans les client components | UX | Standard Qdrant + prompt |

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
user_flows[] extrait par Architect, Journey Validator opérationnel (2/2 flows=100%),
seuil valeur client (spec_coverage > 80% ET user_flows_covered > 60%).

### Pré-Sprint 4.6 ✅ ABSORBÉ (27–28 Mars 2026)
Refactorisation Architecture Simplifiée : LLM supervisors inline supprimés,
supervision déterministe uniquement (tsc + build + quality_check.mjs).

### Sprint 4.6 ❌ ABANDONNÉ — Décision définitive
Les agents LLM inline (conformity_activity, security_activity, architecture_activity)
ont été supprimés. Raison : coût/fiabilité défavorables, même modèle générant et
reviewant partage les mêmes angles morts. Remplacés par supervision déterministe.
**Remplacement prévu : Sprint 4.8 (reviewer post-build, architecture différente).**

### Refactorisation T2-T5 ✅ (Mai 2026)
T2 : agents/core/ (6 modules stack-agnostiques extraits)
T3 : StackAdapter pattern (dev_test_activity multi-stack ready)
T4 : Docker npm_cache (cp node_modules ~7s)
T5 : forbidden_keywords wired dans architect_activity
architect_enhancer.py : inject_prisma_relations extrait de architect.py

---

## SPRINT 4.8 — Reviewer Sémantique Post-Build
## Deadline : Mai 2026 | STATUT : Planifié

### Objectif
Combler le gap entre "forme" (déterministe) et "sens" (sémantique) dans la validation.
Le reviewer tourne APRÈS le build, une seule fois, sur l'ensemble des fichiers générés.
Non bloquant en phase calibration. Alimente directement le Learner.

### Pourquoi pas inline (leçon Sprint 4.6)
Sprint 4.6 a échoué parce que superviser fichier par fichier, avec le même modèle,
crée une boucle de correction infinie. Le reviewer post-build a un scope clos :
les fichiers sont fixés, le build a réussi, la revue est une mesure — pas une correction
en temps réel. C'est architecturalement plus sain.

### Architecture

```
dev_test_activity (build + TSC + quality_check)
        ↓
review_activity (NEW)
  ├── Scope : fichiers business uniquement (app/api/ + app/**/page*.tsx + lib/services/)
  ├── Modèle : gpt-4o-mini (reviewer ≠ générateur — modèle différent évite les angles morts)
  ├── RAG : ZONE_SEC (security patterns) + ZONE_CONF (conformity patterns)
  ├── Checks sémantiques :
  │     • IDOR : tout update/delete vérifie-t-il userId dans le where ?
  │     • Ownership : getAll filtre-t-il par userId ? (pas d'exposition cross-user)
  │     • Auth guard : toute action mutante a-t-elle un await auth() en tête ?
  │     • Brief conformité : les entités du brief sont-elles toutes représentées ?
  ├── Output : ReviewReport {file, issue_type, severity, evidence, suggestion}
  ├── Mode : advisory (non-bloquant) — findings loggés dans run_report + shadow log
  └── Learner pipeline : findings → StandardSuggestion → approve_suggestion.py → Qdrant
        ↓
qa_activity (génération tests e2e)
        ↓
github_activity (push + PR)
        ↓
learner_activity
```

### Règles d'activation progressive
- Phase calibration (10 premiers runs) : advisory seulement, tous findings loggés
- Phase validation (runs 11-30) : si précision > 80% sur les findings → passer en bloquant
  pour severity="critical" uniquement (IDOR, missing auth)
- Phase production : bloquant sur critical, advisory sur medium/low

### Métriques shadow log
```json
{
  "review_findings_count": 3,
  "review_critical_count": 1,
  "review_medium_count": 2,
  "review_precision_estimated": null,
  "reviewer_model": "gpt-4o-mini",
  "files_reviewed": 12
}
```

### Ce que le reviewer NE fait PAS
- Ne relit pas les fichiers template (middleware.ts, jest.config.js, etc.)
- N'appelle pas un deuxième LLM pour "re-générer" les fichiers défectueux
- Ne remplace pas tsc, prisma validate, quality_check.mjs (ils continuent)

### Signal clôture Sprint 4.8
- review_activity opérationnel (Temporal Activity dédiée)
- ZONE_SEC + ZONE_CONF créées dans Qdrant (≥5 standards chacune avec GOOD:/BAD:)
- ≥1 finding IDOR détecté et transmis au Learner sur les runs de test
- ≥1 StandardSuggestion générée depuis un finding reviewer
- Workflow : dev_test → review → qa → github → learner câblé

---

## SPRINT 5 — QA + GitHub Repair + Mode Replay + Standards Maintenance
## Deadline : Juin 2026 | STATUT : Planifié

### 5A — Réparer QA et GitHub (prérequis pipeline complet)

**QA agent :**
- Fix parsing : remplacer le fallback "strict TypeScript" par extraction robuste
  (parse les blocs ```typescript dans la réponse LLM si JSON échoue)
- Prompt QA : forcer output JSON schema strict `{filepath: content}`
- Calibrer : tester sur 5 runs, vérifier que les tests générés correspondent
  aux routes réelles (combined_files passé en contexte — déjà implémenté Sprint 4)
- Signal : `[QA] N tests générés` visible dans les logs sur 3 runs consécutifs

**GitHub agent :**
- Docker Compose : injecter GITHUB_TOKEN dans l'env du container factory-worker
- Test unitaire : vérifier que l'activity produit un pr_url réel sur un repo de test
- Signal : `[GitHub] PR créée → https://github.com/...` visible dans les logs

### 5B — Mode Replay

Si run N échoue et run N-1 réussissait, comparer :
- Fichiers générés (diff) — quelles sections ont divergé ?
- Standards RAG récupérés (quels IDs Qdrant) — un standard a-t-il changé ?
- Décisions LLM (patches appliqués) — où la divergence s'est-elle produite ?

Outil de debugging radical pour identifier les standards insuffisants.
Prérequis : run_id propagé partout (déjà fait) + rag_usage.jsonl avec IDs Qdrant réels.

### 5C — StandardsMaintenanceAgent (Web Search → Standard)

Quand le Learner détecte un pattern récurrent (N ≥ 3 occurrences) :
1. StandardsMaintenanceAgent cherche sur le web (Tavily API) — sources officielles uniquement
   ```
   ALLOWLIST : nextjs.org | clerk.com | prisma.io | jestjs.io
   ```
2. LLM génère standard prescriptif (RULE:/WHY:/GOOD:/BAD:) depuis les résultats
3. Mode Replay valide que le standard corrige le run défaillant
4. Écriture dans learner_suggestions.json (PAS Qdrant direct)
5. Validation humaine → approve_suggestion.py → upsert Qdrant

### 5D — Compatibility Matrix dynamique

Remplace VERSION_PINS hardcodés dans le code :
```json
{"next": "14.2.25", "clerk": "6.x", "prisma": "7.x"} → "validated"
{"next": "15.x",    "clerk": "6.x", "prisma": "7.x"} → "experimental"
```
Critère promotion : 2 runs build_success=true → "validated"
Critère dégradation : 3 runs build_success=false → "unstable"

### Signal clôture Sprint 5
- QA agent : tests générés sur 3 runs consécutifs, routes réelles uniquement
- GitHub agent : PR créée visible dans Temporal dashboard
- Mode Replay opérationnel (comparaison run N vs N-1)
- ≥1 standard créé depuis web search + validé humainement + upsert Qdrant
- ≥1 hook supprimé ou renforcé grâce au standard web-search

---

## SPRINT 6 — Apps Niveau B/C : Fondations
## Deadline : Juillet 2026 | STATUT : Planifié

### Contexte

Les apps actuelles sont de niveau A (SaaS simple : auth + CRUD + dashboard).
Le niveau B = Multi-tenant SaaS (Notion, Slack, Figma clone — workspaces/organisations).
Le niveau C = Marketplace/Platform (Etsy, Airbnb, Upwork — deux acteurs).

L'architecture StackAdapter + agents/core/ pose exactement la bonne fondation.
Ajouter une stack B ou C = nouveau StackAdapter + JSON + générateurs déterministes.
Zéro modification du moteur (dev_test_activity, architect_activity, workflow).

### 6A — ProjectSpec étendu

Nouveaux champs dans `agents/project_spec.py` (rétrocompatibles — défaut = False/"") :
```python
organizations: bool = False         # Clerk Orgs — multi-tenant
roles: list[str] = []               # ["OWNER", "ADMIN", "MEMBER"]
billing_provider: str = ""          # "stripe"
actors: list[str] = []              # ["BUYER", "SELLER"] marketplace
```

### 6B — Générateur Membership (déterministe — niveau B)

`agents/stacks/nextjs_clerk_prisma/dev_membership_generator.py`
Génère :
- `lib/services/membership.service.ts` : joinOrg, leaveOrg, getMembers, checkRole
- `lib/permissions.ts` : isOwner(), isAdmin(), requireRole() guards
- Injection automatique de `orgId` sur chaque entité via `inject_relations` hook
- Template `middleware.ts` étendu avec routing Clerk Orgs

### 6C — Stack `nextjs-clerk-orgs-prisma`

```
agents/stacks/nextjs_clerk_orgs_prisma/
  __init__.py
  adapter.py          ← StackAdapter, stack_id = "nextjs-clerk-orgs-prisma"
  architect_enhancer.py  ← inject_org_relations() + inject_membership_model()
  dev_graph.py        ← extends nextjs-clerk-prisma avec membership generator
config/stacks/nextjs-clerk-orgs-prisma.json
```

Le `adapter.inject_relations()` ajoute automatiquement :
- Model `Membership { userId, orgId, role, createdAt }`
- `orgId String` sur chaque entité business
- Relations Membership ↔ entité

### 6D — Brief IR Multi-tenant

Le `planner_node` dans `architect.py` doit lire les nouveaux champs :
```python
if brief.get("organizations"):
    spec = spec.with_organizations(brief.get("roles", ["OWNER", "MEMBER"]))
```

### Signal clôture Sprint 6
- ProjectSpec étendu (organizations/roles/actors/billing_provider) sans régression
- dev_membership_generator.py opérationnel
- Stack nextjs-clerk-orgs-prisma : ≥1 run build_success=true sur un brief Notion/Slack clone
- Membership table + orgId présents dans le schéma Prisma généré
- permissions.ts avec requireRole() généré correctement

---

## SPRINT 7 — Multi-tenant SaaS Complet + Billing
## Deadline : Août 2026 | STATUT : Planifié

### 7A — Stripe Billing (level B)

`agents/stacks/nextjs_clerk_prisma/dev_billing_generator.py`
Génère :
- `app/api/billing/route.ts` : création subscription Stripe
- `app/api/webhooks/stripe/route.ts` : gestion événements Stripe
- `lib/stripe.ts` : client Stripe (template)
- `.env.local` étendu : STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET, NEXT_PUBLIC_STRIPE_KEY

Brief IR : `billing_provider: "stripe"` active le générateur.

### 7B — RBAC Guards dans les templates

`middleware.ts` template étendu pour routing par rôle Clerk :
```typescript
// Généré si organizations=true dans le brief
export function middleware(req: NextRequest) {
  const { orgRole } = auth();
  if (req.nextUrl.pathname.startsWith('/admin') && orgRole !== 'org:admin') {
    return NextResponse.redirect('/unauthorized');
  }
}
```

### 7C — Dashboard Gouvernance + Stack Manager

Interface web de gestion :
- Voir/modifier config/stacks/*.json actives
- Voir les standards Qdrant par stack
- Créer une nouvelle stack (formulaire → génère JSON)
- Voir les métriques du reviewer sémantique par run

### 7D — SanitizerRegistry (migration dette technique)

Les sanitizers hardcodés dans shared_tools.py (`_remove_pages_router_conflicts`,
`_ensure_layout_html_body`, etc.) migrés vers une registry déclarative :
```json
"sanitizers": ["NextjsRemovePagesConflicts", "NextjsEnsureHtmlBody", ...]
```
Python itère sur la liste et dispatche. Zéro logique stack-specific en Python.

### Signal clôture Sprint 7
- ≥1 run Notion clone (workspaces + members + RBAC) avec build_success=true
- Stripe subscription flow généré sur un brief avec `billing_provider: "stripe"`
- SanitizerRegistry opérationnel (≥3 sanitizers migrés)
- Dashboard Gouvernance accessible sur http://localhost:3001

---

## SPRINT 8 — Marketplace/Platform (Level C) + Stack Versioning
## Deadline : Septembre 2026 | STATUT : Planifié

### 8A — Stack `nextjs-marketplace-prisma`

Two-actor spec : BUYER et SELLER avec flows distincts.
Modèles générés déterministiquement :
- `Listing { id, sellerId, title, price, status }`
- `Order { id, buyerId, listingId, quantity, status }`
- `Review { id, buyerId, listingId, rating, comment }`

Stripe Connect : paiements séparés par vendeur (dev_billing_generator étendu).

### 8B — Brief Two-Actor

```python
# ProjectSpec étendu
actors: list[str] = ["BUYER", "SELLER"]
# Planner génère automatiquement :
# - Pages /buyer/dashboard, /seller/dashboard
# - Routes séparées par acteur
# - Middleware routing par rôle acteur
```

### 8C — Stack Versioning

```
nextjs-clerk-prisma@1.0 → next@14.2.25 (stable)
nextjs-clerk-prisma@2.0 → next@15.x    (quand stable)
```
Un projet généré est lié à la version de stack utilisée.
Rollback possible si nouvelle version crée des régressions.
Compatibility Matrix (Sprint 5) pilote les promotions automatiquement.

### Signal clôture Sprint 8
- ≥1 run Etsy/Airbnb clone (BUYER/SELLER, listings, orders) avec build_success=true
- Stripe Connect flow généré
- Stack versioning opérationnel (`.factory-meta.json` par projet avec version stack)

---

## SPRINT 9 — Production Ready
## Deadline : Octobre 2026 | STATUT : Planifié

### Objectifs
- Vercel Preview Deploys automatiques depuis github_activity
- Playwright E2E sur les apps déployées (QA agent étendu)
- Démo 50 projets autonomes (A + B + C niveaux)
- Metrics dashboard public : build_success_rate, security_score, spec_coverage

### Multi-stack full (≥2 stacks en production)
Avec Stack-as-Config + StackAdapter en place :
- Stack 2 : `vue-fastapi-sqlalchemy` — estimation <5% Python core modifié
- Stack 3 : `nextjs-supabase` (alternative à Clerk+Prisma)

---

## JALONS v3.0

| Date cible | Livrable | Signal mesurable | Statut |
|------------|----------|-----------------|--------|
| Mars 2026 | Sprint 2 | build_success + tests_passed reproductibles | ✅ |
| Mars 2026 | Sprint 3 | qdrant_filter + commands JSON + LearnerActivity | ✅ |
| Avril 2026 | Sprint 4 | Gate décisionnel + anti-patterns + contracts v2 | ✅ |
| Avril 2026 | Sprint 4.5 | Journey Validator + user_flows + spec_coverage | ✅ |
| Mai 2026 | Refacto T2-T5 | agents/core/ + StackAdapter + T4 Docker | ✅ |
| Mai 2026 | Sprint 4.8 | Reviewer sémantique post-build + ZONE_SEC/CONF | ⏳ |
| Juin 2026 | Sprint 5 | QA+GitHub réparés + Mode Replay + web search | ⏳ |
| Juillet 2026 | Sprint 6 | Level B fondation — multi-tenant build_success | ⏳ |
| Août 2026 | Sprint 7 | Stripe billing + RBAC + Dashboard Gouvernance | ⏳ |
| Sept 2026 | Sprint 8 | Level C marketplace — Etsy/Airbnb clone | ⏳ |
| Oct 2026 | Sprint 9 | 50 projets autonomes A+B+C, Vercel deploy | ⏳ |

---

## DETTE TECHNIQUE CONNUE (non bloquante)

| # | Description | Sprint cible |
|---|-------------|-------------|
| D1 | `(data as any)` dans les services générés | Standard Qdrant Sprint 4.8 |
| D2 | IDOR sur update (missing userId dans where) | Reviewer Sprint 4.8 |
| D3 | updatedAt manquant sur Project/Task/Comment | dev_service_generator Sprint 5 |
| D4 | Pagination hardcodée `take:20` | Standard Qdrant Sprint 5 |
| D5 | User model orphelin (no FK vers entités) | Design decision Sprint 6 |
| D6 | AST engine placeholder dans dev.py | Sprint 7+ (si besoin confirmé) |
| D7 | test_sprint1_validation.py legacy | Archiver Sprint 5 |
| D8 | learner_agent_contract.json zombie | Supprimer Sprint 5 |

---

## DÉCISIONS ARCHITECTURALES (log permanent)

| Date | Décision | Raison |
|------|----------|--------|
| Fév 2026 | Stack-as-Config JSON | PRINCIPE 1 — zéro logique stack en Python |
| Mars 2026 | Guards regex → WARN | TypeScript/Prisma sont arbitres — les guards informent |
| Mars 2026 | Sprint 4.6 abandonné | LLM inline supervisors : même modèle, mêmes angles morts |
| Mars 2026 | requirements[] déterministe | JAMAIS depuis plan LLM — élimine ghost success |
| Avril 2026 | StackAdapter pattern | Multi-stack sans toucher au moteur — T3 |
| Avril 2026 | agents/core/ extraction | Stack-agnostique — réutilisable par toute future stack |
| Mai 2026 | Reviewer post-build | Scope clos, modèle différent, advisory → PRINCIPE 4 |
| Mai 2026 | Déterministe ≠ supprimé | Le déterministe se concentre sur la forme, l'agentique sur le sens |
