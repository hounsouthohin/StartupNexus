# Software Agent Factory — Carte de graduation des applications
## Version 2.0 — Mise à jour 6 Juillet 2026 (post-lecture complète 8 niveaux)
## Historique : v1.0 (Mai 2026) · v2.0 (6 Juil 2026 — états L1-L16 vérifiés dans le code, chemin de graduation recalculé, règle des 4 lots)

---

###### FRONTEND

Niveau frontend par type d'app
| Type | Qui voit l'app | Niveau frontend nécessaire |
|---|---|---|
| A | Le propriétaire (lui seul) | Shell propre + tables lisibles + formulaires corrects. Rien de plus. |
| D | L'auteur (privé) + les visiteurs (public) | Premier type où la qualité visuelle compte — le public voit le résultat |
| I | Employés + managers | Shell + StatusFlow (filtres, badges d'approbation, boutons de transition) |
| K | Admin + utilisateurs | Nav conditionnelle par rôle, guards visuels |
| H | Analysts internes | Charts (recharts) — StatCards avancées |
| G | Clients + staff | Shell + CalendarView — la vue calendrier est le cœur de l'app |
| E | Acheteurs (public) | Grille produits, pages publiques polished |
| F | Utilisateurs grand public | Feed, profils — UX grand public |
| B+ | Équipes | Workspace selector, navigation complexe |

---

## 1. Types d'applications cibles (stack nextjs-clerk-prisma)

| Code | Type | Exemples |
|---|---|---|
| A | CRUD SaaS simple | project-hub, contact-crm, leave-manager, invoice-tracker |
| B | Multi-tenant SaaS | Notion, Slack, Figma clone — workspaces/organisations |
| C | Marketplace / Platform | Etsy, Airbnb, Upwork clone — deux côtés |
| D | Blog / CMS | Medium clone, documentation, publishing workflow |
| E | E-commerce | Boutique, catalogue, panier, commandes |
| F | Social / Communauté | Feed, likes, follows, commentaires, notifications |
| G | Booking / Calendrier | Prise de RDV, disponibilités, créneaux |
| H | Dashboard / Analytics | Métriques, agrégations, séries temporelles |
| I | Workflow / Approbation | Processus RH, validation commandes, review content |
| J | Gestion de fichiers/documents | Uploads, versioning, permissions fichiers |
| K | Multi-Role / RBAC | Admin dashboard + portail utilisateur, manager + employé, éditeur + lecteur |

---

## 2. État actuel — Juillet 2026

### Type A — VALIDÉ ✅
7+ projets BUILD_SUCCESS (project-hub, task-manager, leave-manager, learn-hub, recipe-manager, expense-tracker, app-simple) + 3 runs récents 3/3 (writer-pad, freelance-tracker, sprint-board).

### Type D — À 80% ✅ (writer-pad, Juillet 2026)
writer-pad prouve : pages publiques + privées mixtes, slug routing, published Boolean, dual-nav (TopNavShell public / DashboardShell privé), design preset editorial. **Restent : SEO, many-to-many (tags), rich textarea.**

### Capacités transverses acquises depuis la v1.0
- 3 enums Prisma sur un même modèle (sprint-board) + labels traduits (enum_value_labels → badges + selects)
- FK chains 3 niveaux avec detail_with_children (freelance-tracker : Client → Project → Invoice)
- Design system déterministe : 7 presets domaine + CSS variables + shadcn/ui
- Design Brief LLM (icônes/badges/layouts par entité) + Page Enricher TSC-guardé
- Reviewer deux couches (Layer 1 déterministe IDOR/CROSS_USER/AUTH + Layer 2 LLM sémantique)
- Plan-and-Execute dev LLM : contexte par fichier (context_hint + pages_detail + page contracts + RAG par rôle + example anchoring)

---

## 3. Chemin de graduation — RECALCULÉ (Juillet 2026)

```
A (validé) → D-complet → I → K → H → G → E → F → B → C → J
```

**Pourquoi ce nouvel ordre (ancien : A→D→K→G→I) :** la lecture du code (6 Juil 2026) montre que les
limitations bloquantes déclarées pour I (L8 enums, L6 filtrage) sont **déjà résolues**, tandis que K
introduit un concept (rôle) absent des 8 niveaux du pipeline, et G exige la logique métier temporelle
la plus lourde (conflits de créneaux + CalendarView inexistante). L'ordre suit la complexité IA
croissante : D ≈ 0% de travail prompt, I ≈ 20%, K ≈ 40%, H ≈ 50%.

---

## 3.5. RÈGLE DES 4 LOTS — obligatoire pour toute expansion

Une expansion n'est PAS un générateur. Chaque nouveau type livre **4 lots synchronisés** —
jamais l'un sans les autres :

| Lot | Contenu | Fichiers types |
|---|---|---|
| **1 — Squelette** | Modules service/feature + templates Jinja2 + champs ProjectSpec + flags ModelGenerationContext | `service_modules/*.py`, `feature_modules/*.py`, `templates/*.j2`, `project_spec.py`, `dev_model_context.py` |
| **2 — Connaissance** | Few-shots architect (domain_interpreter + page_planner) + annotations semantic_annotator + standards Qdrant + CONTEXT_QUERY + **mise à jour** (pas juste ajout) de rules_dev.md | `domain_interpreter.py`, `page_planner.py`, `architect.py`, `create_full_standards_v1.py`, `dev_prompts.py`, `rules_dev.md` |
| **3 — Design** | Archétypes design_brief (icônes/layouts du type) + preset si nouveau domaine | `dev_design_brief.py`, `design_presets.json` |
| **4 — Garde-fous** | Check reviewer Layer 1 + entrée SERVICE_METHOD_REGISTRY (propage auto vers architect + spec_enricher) | `reviewer.py`, `service_modules/__init__.py` |

**Passe de cohérence finale obligatoire** : relire rules_dev.md + CONTEXT_QUERIES +
build_factory_capabilities_string + standards Qdrant → aucune instruction ancienne ne doit
contredire la nouvelle capacité. Exemple de piège réel : rules_dev.md règle 12 dit
« agrégations = getAll + calcul TypeScript » — contradiction directe avec le futur
AggregationModule du Type H si non réécrite.

**Mécanisme d'auto-propagation (à exploiter)** : toute méthode ajoutée dans
`SERVICE_METHOD_REGISTRY` est automatiquement connue de l'architect
(via build_factory_capabilities_string) et validée par le spec_enricher — zéro modification
de prompt architecte nécessaire pour les méthodes de service.

---

## 4. Carte détaillée par type

### Phase 2 — Type D-complet : Blog / CMS *(80% fait)*
**Nouveauté critique :** SEO + relations many-to-many (tags).

État des limitations :
| Limite | Description | État |
|---|---|---|
| L3 | Services sans filtre userId pour modèles publics | ✅ RÉSOLU (PublicModule) |
| L14 | getBySlug | ✅ RÉSOLU (SlugModule) |
| L8 | Enums → string | ✅ RÉSOLU (spec.enums + z.enum + enum-select) |
| L5 | Tri par createdAt DESC | ✅ RÉSOLU (orderBy dans getPublished/getPublicAll) |
| **L11** | **Many-to-many ignoré (Post ↔ Tag)** | ❌ À faire |
| **SEO** | **metadata, og:image, sitemap.xml** | ❌ À faire (dev_seo_generator) |

4 lots :
- **Lot 1** : `dev_seo_generator.py` (metadata + sitemap), extension relations M2M dans service_modules, template `rich_textarea` pour champ content
- **Lot 2** : ~6 standards (SEO metadata, draft/publish lifecycle, M2M tags) — architect connaît déjà editorial/slug/public
- **Lot 3** : rien (preset editorial + layout hero existants)
- **Lot 4** : rien de nouveau (checks publics existants)

**Débloque :** blogs complets, portfolios avec tags, documentation, wikis.

---

### Phase 3 — Type I : Workflow / Approbation *(quasi débloqué)*
**Nouveauté critique :** machine à états (FSM) — transitions de statut légales uniquement.

État des limitations :
| Limite | Description | État |
|---|---|---|
| L8 | Enums | ✅ RÉSOLU |
| L6 | Filtrage par statut | ✅ RÉSOLU (module_status_flow) |
| **FSM** | **Aucune validation de transition — update direct du status possible** | ❌ Le cœur du type |

4 lots :
- **Lot 1** : `service_modules/transition.py` (TransitionModule → `transitionTo(userId, id, newStatus)` avec table des transitions légales), champ `status_transitions` dans ProjectSpec, boutons de transition dans template détail
- **Lot 2** : semantic_annotator annote les transitions légales (extension du status-enum qui extrait déjà l'ordre workflow), few-shot congés dans domain_interpreter, ~8 standards (FSM pattern, anti-update-direct), CONTEXT_QUERY `workflow-pages`
- **Lot 3** : rien (conventions badges pending/approved/rejected déjà dans design_brief)
- **Lot 4** : check reviewer « update direct du champ status hors transitionTo » + entrée registre `if_transitions`

**Débloque :** workflows RH, validation de commandes, review de contenu, approbations.

---

### Phase 4 — Type K : Multi-Role / RBAC
**Nouveauté critique :** rôles via Clerk `publicMetadata.role` — routes, services et navigation varient selon le rôle. Concept absent des 8 niveaux aujourd'hui → vrai chantier de connaissance (Lot 2 dominant).

| Limite | Description | État |
|---|---|---|
| LK1 | Aucune logique de rôle dans middleware.ts | ❌ |
| LK2 | Pas de getAllAsAdmin() ni guard rôle dans les services/actions | ❌ |
| LK3 | Nav sidebar fixe, aucune branche par rôle | ❌ |
| LK4 | Pas de flow d'assignation de rôle | ❌ |

4 lots :
- **Lot 1** : `dev_rbac_generator.py` (guards rôle dans Server Actions + getAllAsAdmin), extension middleware template, nav conditionnelle dans layout generator, champ `roles: []` dans ProjectSpec
- **Lot 2** : **le plus gros lot** — few-shots admin/portail dans domain_interpreter ET page_planner (pattern /admin/*), standards LK1-LK4, règle rules_dev « page admin vérifie le rôle », CONTEXT_QUERY `admin-pages`, nuance brief_guide (un seul propriétaire de données, plusieurs niveaux de lecture)
- **Lot 3** : nav_icons admin dans design_brief
- **Lot 4** : **OBLIGATOIRE avant le 1er run** — check reviewer « page /admin sans vérification de rôle » (faille sécurité sinon silencieuse)

Note : l'invariant single-tenant (userId sur tous les modèles) n'est PAS violé par K — l'admin
est un lecteur privilégié, pas un second propriétaire. C'est B qui casse l'invariant, pas K.

**Débloque :** admin + portail utilisateur, manager + employé, éditeur + lecteur.

---

### Phase 5 — Type H : Dashboard / Analytics *(le type le plus agentique)*
**Nouveauté critique :** agrégations Prisma (count, sum, avg, groupBy) + composition visuelle libre (recharts).

| Limite | Description | État |
|---|---|---|
| L13 | Pas de méthodes d'agrégation | ❌ Bloquant (type entier) |
| L4 | Pas de pagination | ❌ (partiel : getPublished paginé) |
| L12 | Json → unknown | ❌ |

4 lots :
- **Lot 1** : `service_modules/aggregation.py` (count/sum/avg/groupBy selon annotation `analytics`), StatCard enrichi, pagination getAll
- **Lot 2** : ⚠ **RÉÉCRIRE rules_dev règle 12** (contradiction sinon), annotation `kpis` dans semantic_annotator, standards charts/recharts, CONTEXT_QUERY `analytics-pages`
- **Lot 3** : archétype chart_type par entité dans design_brief + recharts dans package template
- **Lot 4** : entrée registre `if_analytics` + check N+1 sur les pages dashboard

**Débloque :** tableaux de bord de métriques, reporting, analytics internes.

---

### Phase 6 — Type G : Booking / Calendrier
**Nouveauté critique :** logique métier temporelle (conflits de créneaux, disponibilités) + CalendarView (composant UI inexistant). Réutilise la FSM du Type I (pending → confirmed → cancelled).

| Limite | Description | État |
|---|---|---|
| L5/L6 | Tri + filtrage par date | ✅/partiel |
| Conflits | Détection de chevauchement de créneaux | ❌ Nouveau territoire métier |
| CalendarView | Vue calendrier | ❌ Signal `calendar_view` déclaré dans le catalogue features mais AUCUN module ne l'implémente |

**Débloque :** prise de RDV, plannings, réservations.

---

### Phase 7 — Type E : E-commerce
3 chantiers indépendants : L10 (Decimal non sérialisé), L15 ($transaction Order+Items), Stripe (intégration externe + webhooks). Réutilise D (catalogue public + slug) et H (agrégations totaux).

### Phase 8 — Type F : Social
L11 (M2M — hérité de D-complet), L4 (pagination feed — héritée de H), compteurs (L13 — hérités de H).

### Phase 9 — Type B : Multi-tenant ⚠ SAUT ARCHITECTURAL
L2 : owner = userId **hardcodé dans l'invariant du domain_interpreter** (« TOUS les modèles DOIVENT avoir userId String »). Casser cet invariant touche le prompt architect, le ProjectSpec, tous les service_modules et le reviewer. À faire en DERNIER des types fondamentaux, avec une batterie de tests de non-régression sur les types A→H.

### Phase 10 — Types C (Marketplace = D+E+B) et J (Fichiers = intégration S3/R2 externe)

---

## 5. Tableau de synthèse — phases

| Phase | Type | Travail restant | Part IA du travail | Apps débloquées |
|---|---|---|---|---|
| 1 ✅ | A | — | — | CRM, HR, billing, gestion |
| 2 | **D-complet** | SEO + M2M + rich textarea | ~0% | blogs, CMS, portfolios, wikis |
| 3 | **I** | TransitionModule + transitions annotées | ~20% | approbations, workflows RH |
| 4 | **K** | RBAC generator + few-shots admin | ~40% | admin+portail, manager+employé |
| 5 | **H** | AggregationModule + réécriture règle 12 | ~50% | dashboards, reporting |
| 6 | G | Conflits créneaux + CalendarView | ~30% | booking, plannings |
| 7 | E | Decimal + $transaction + Stripe | ~30% | boutiques |
| 8 | F | Feed + compteurs (hérite D+H) | ~30% | communautés |
| 9 | B | Casser invariant single-tenant | ~60% | multi-tenant SaaS |
| 10 | C, J | Combinaisons + intégrations externes | — | marketplaces, GED |

---

## 6. Audit des limites déterministes (états vérifiés dans le code — 6 Juil 2026)

| # | Limite | État | Preuve code |
|---|---|---|---|
| L1 | Omit<PrismaType> Prisma 7 | ✅ Corrigé Sprint 2 | dev_types_generator énumère les champs |
| L2 | Owner = userId hardcodé | ❌ Phase 9 (B) | invariant domain_interpreter + _resolve_owner |
| L3 | Modèles publics | ✅ RÉSOLU | PublicModule (getPublicAll/getPublicById) + has_public_pages |
| L4 | Pagination | ⚠ Partiel | getPublished paginé ; getAll non — Phase 5 |
| L5 | Tri | ✅ RÉSOLU | orderBy createdAt desc dans les modules publics |
| L6 | Filtrage par statut | ✅ RÉSOLU | module_status_flow (filtre client) + required_queries |
| L7 | Relations 1 niveau | ⚠ Partiel | getByIdWithRelations 1 niveau — suffisant jusqu'à E |
| L8 | Enums → string | ✅ RÉSOLU | spec.enums → z.enum + enum-select + enum_value_labels |
| L9 | Soft delete | ❌ Phase 7+ | _AUTO_FIELDS exclut deletedAt mais aucun where deletedAt:null |
| L10 | Decimal non sérialisé | ❌ Phase 7 (E) | _serialize ne touche que DateTime |
| L11 | Many-to-many | ❌ Phase 2 (D-complet) | is_array → skip dans editable_fields |
| L12 | Json → unknown | ❌ Phase 5+ | _PRISMA_TO_TS mappe Json → unknown |
| L13 | Agrégations | ❌ Phase 5 (H) | aucun module aggregate |
| L14 | getBySlug | ✅ RÉSOLU | SlugModule (3 méthodes : getBySlug, getBySlugOwned, getBySlugWithRelations) |
| L15 | Create atomique $transaction | ❌ Phase 7 (E) | un seul prisma.create par module |
| L16 | Actions 100% LLM | ✅ Corrigé Sprint 4 | dev_actions_generator déterministe |
| LK1-4 | RBAC | ❌ Phase 4 (K) | le mot « role » absent de tous les générateurs |
| FSM | Transitions non validées | ❌ Phase 3 (I) | update() accepte n'importe quel status |

---

## 7. Briefs de test par phase (à exécuter pour valider chaque type)

| Phase | Brief de validation | Signal de succès |
|---|---|---|
| 2 (D) | Blog avec tags M2M, SEO, draft/publié, contenu long | build + sitemap.xml + tags fonctionnels + `is_useful_app: true` |
| 3 (I) | Demandes de congé : employé soumet, manager approuve/rejette | transition illégale refusée par le service + boutons UI corrects |
| 4 (K) | SaaS admin+user : admin voit tout, user voit ses données | reviewer 0 finding rôle + nav différente par rôle |
| 5 (H) | Dashboard commercial : CA du mois, taux de conversion, chart évolution | agrégations en DB (pas de getAll+filter) + recharts rendu |
