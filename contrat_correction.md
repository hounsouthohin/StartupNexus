# CONTRAT DE CORRECTION — définition de « app parfaite » par type
> Ce que la factory DOIT garantir pour qu'un type soit VRAIMENT « terminé ».
> Chaque invariant a soit une **garantie déterministe** (générateur), soit un **check reviewer**.
> Un invariant sans l'un ni l'autre = TROU : « terminé » est faux tant qu'il existe.
> Vérifié contre le code réel — 8 Juillet 2026. (Statuts : ✅ garanti · ⚠️ partiel · ❌ trou)

## Règle du contrat
Un type n'est « terminé » que lorsque **chaque invariant de sa colonne est ✅**.
« Le build passe » et « les pages du spec existent » ne sont PAS des preuves de correction —
ce sont des preuves de forme. Le contrat teste la correction.

---

## TYPE A — CRUD SaaS privé mono-utilisateur

### Sécurité / isolation
| # | Invariant | Garantie / Check | Statut |
|---|---|---|---|
| S1 | Toute lecture filtre par owner (`findMany where {userId}`) | crud.py + reviewer `_check_service_cross_user` | ✅ |
| S2 | `update`/`delete` portent `where {id, userId}` (jamais `id` seul) | crud.py + reviewer `_check_service_idor` | ✅ |
| S3 | `userId` injecté côté serveur (jamais depuis le formData client) | crud.py `data:{...data, userId}` + actions | ✅ |
| S4 | `userId` exclu du retour service (SerializedXxx) | `_serialize` retire l'owner | ✅ |
| S5 | Toute page privée a le guard `auth()` + redirect | pages_generator + reviewer `_check_page_auth` | ✅ |
| S6 | Création/MAJ avec FK : la FK référencée appartient au owner | crud.py : garde `findFirst({id, owner})` + throw avant insert (8 Juil) | ✅ |

### Validation des entrées
| # | Invariant | Garantie / Check | Statut |
|---|---|---|---|
| V1 | Champs requis non vides (`.min(1)`) | dev_zod_generator | ✅ |
| V2 | Enums restreints aux valeurs autorisées (`z.enum`) | dev_zod_generator | ✅ |
| V5 | Types numériques coercés (`z.coerce.number`) | dev_zod_generator | ✅ |
| V3 | Champ email validé comme email (`.email()`) | dev_zod_generator `_semantic_zod` — nom du champ + annotation (8 Juil) | ✅ |
| V4 | Nombre à sémantique bornée validé (prix/distance `>= 0`) | dev_zod_generator — nom (suffixe camelCase) + `currency` (8 Juil) | ✅ |

### Données (requêtes, sérialisation, agrégats)
| # | Invariant | Garantie / Check | Statut |
|---|---|---|---|
| D1 | DateTime sérialisé en ISO string | `_serialize` / maps base.py | ✅ |
| D2 | Decimal sérialisé en number | `_serialize` + maps (fix 7 Juil) | ✅ |
| D3 | Relations chargées quand demandées (WithRelations) | relations.py | ✅ |
| D4 | Un agrégat (total/count dashboard) porte sur l'ENSEMBLE, pas une page | dev_graph : les sources KPI sont dé-paginées (pageSize élevé) dans l'appel service (8 Juil) | ✅ |
| **D5** | **Tri par défaut a un sens métier** | ⚠️ `createdAt desc` codé en dur — OK par défaut, faux pour données à date | ⚠️ partiel |

### Conformité / intégrité
| # | Invariant | Garantie / Check | Statut |
|---|---|---|---|
| C1 | Chaque page du brief existe et appelle son service | pages_generator + spec_coverage | ✅ |
| **C2** | **Suppression en cascade signalée à l'utilisateur** | ⚠️ `onDelete:Cascade` + `confirm()` générique sans mention | ❌ **TROU** |

---

## TYPE D — Blog/CMS (hérite de TOUS les invariants A + les suivants)

### Sécurité / isolation (public)
| # | Invariant | Garantie / Check | Statut |
|---|---|---|---|
| S7 | Modèles publics : `getPublic*` sans userId MAIS filtre published/visibility | public.py + status.py | ✅ |
| S9 | Les brouillons ne fuitent jamais côté public | `getPublicAll` filtre `published:true` | ✅ |
| S8 | PII (email/téléphone) jamais rendue sur une page publique | reviewer `_check_public_pii` — regex insensible à la casse, tout préfixe camelCase (8 Juil) | ✅ |
| S10 | M2M `connect`/`set` : les IDs liés appartiennent au owner | crud.py : pré-filtrage `findMany({id:{in}, owner})` → `connect/set _valid_ids` (8 Juil) | ✅ |

### Validation (slug public)
| # | Invariant | Garantie / Check | Statut |
|---|---|---|---|
| V6 | Slug : collision gérée sans échec (pas de P2002 générique) | crud.py : suffixe anti-collision `-2/-3` ; global @unique CONSERVÉ (correct pour URLs publiques partagées, pas per-user) (8 Juil) | ✅ |
| V7 | Slug dérivé du titre (format URL, jamais saisi à la main) | crud.py slugify (accents strippés) + retiré du form/Zod/CreateInput ; fallback manuel si pas de titre (8 Juil) | ✅ |

### Données / conformité (contenu)
| # | Invariant | Garantie / Check | Statut |
|---|---|---|---|
| C3 | SEO : sitemap.ts + robots.ts + generateMetadata présents | dev_seo_generator | ✅ |
| C4 | Contenu long rendu en prose (`whitespace-pre-wrap`) | detail_client.tsx.j2 | ✅ |
| D6 | Liste publique triée par date de publication desc | getPublished orderBy | ✅ |

---

## 3ᵉ COLONNE — CONFORMITÉ FONCTIONNELLE (transversale, tous types)

Distincte des invariants techniques : « l'app fait-elle *tout* ce que le brief demande ? ».
Ne peut PAS être garantie par un générateur (spécifique au brief) → deux leviers :
1. **Structurer les motifs récurrents** (zone 2) : contrats compilés en code exact au lieu de prose.
2. **Reviewer en checklist brief→code** (à construire) : vérifier chaque exigence, pas une impression.

| Motif zone 2 | Contrat | Compilateur | Statut |
|---|---|---|---|
| Chiffre agrégé (total/moyenne/compte) | `KPIDeclaration` | dev_graph → expr TS exacte | ✅ (8 Juil) |
| Liste filtrée (« sous 7 jours », « en retard ») | `FilteredListDeclaration` | dev_graph → `.filter()` exact (eq/within_days/before/after) | ✅ (8 Juil) |
| Tri métier (blog=créa desc, events=date asc) | *SortDeclaration à créer* | — | ⏳ résout D5 proprement |
| Reviewer checklist brief→code | — | reviewer L2 upgrade | ⏳ chantier dédié |

**Anti-biais des prompts (8 Juil)** : pages_detail réécrit (règle abstraite + exemple étiqueté « forme, pas gabarit » + contradiction prose/structure supprimée) ; étiquette anti-ancrage ajoutée à domain_interpreter, page_planner, semantic_annotator. Correspond au chantier roadmap « Few-shot → JSON externe » (dimension qualité, pas seulement tokens).

---

## SYNTHÈSE — état des TROUS

| Priorité | Trou | Type | Nature | Fix source |
|---|---|---|---|---|
| ✅ 1 | S6 + S10 — ownership des IDs liés (FK + M2M) sur create/update | A+D | Sécurité | **FAIT 8 Juil** — garde déterministe dans crud.py (FK findFirst+throw, M2M pré-filtre). Pas de check reviewer : redondant sur du déterministe protégé (contrat = garantie OU check) |
| ✅ 2 | V3 + V4 — email/url/nombre validés | A | Validation | **FAIT 8 Juil** — `_semantic_zod` : nom du champ (structurel) + annotation en secours ; conservateur (exclut score/solde/température) |
| ✅ 3 | D4 — agrégats sur l'ensemble | A | Données | **FAIT 8 Juil** — les sources de KPI sont dé-paginées dans l'appel service injecté au dev LLM |
| ✅ 4 | V6 + V7 — slug dérivé + collision | D | Validation | **FAIT 8 Juil** — slugify côté service + suffixe anti-collision + retiré du form. (Analyse : global @unique CORRECT pour blog public, pas per-user comme le rapport suggérait) |
| ✅ 5 | S8 — PII au-delà des marqueurs email/phone | D | Sécurité | **FAIT 8 Juil** — regex insensible casse + préfixes camelCase |
| ⏳ 6 | D5 — tri métier / C2 — avertissement cascade | A | UX/données (mineur) | D5 = futur SortDeclaration (zone 2) ; C2 = confirm() enrichi (différé, multi-templates pour gain mineur) |

**Une fois ces 6 lignes ✅, "Type A terminé" et "Type D terminé" deviennent des affirmations vraies.**
Les types suivants (I, K, H…) héritent de A+D et ajoutent leur propre colonne d'invariants,
écrite AVANT d'implémenter le type (pas après le premier run raté).

---

## TYPE K — RÔLES / MULTI-ACTEUR (hérite de A+D, écrit AVANT implémentation — 26 Juil 2026)

### Le principe fondateur (décision de conception)
> **Un rôle = un ACCÈS PRIVILÉGIÉ dans le MÊME espace de données. PAS du multi-tenant.**
> `userId` reste l'owner (le créateur). Un admin **contourne** le filtre owner pour lire/écrire
> les données de tous. Les membres restent owner-scoped. L'invariant single-tenant n'est donc
> PAS violé : l'admin est un super-lecteur/écrivain, pas un second propriétaire.

### Ce que les 2 sondes ont révélé (le trou, en réel)
- **it-requests (simple)** : l'architect a APLATI « employé vs admin » en mono-acteur, en silence.
  « admin voit toutes les demandes » → `getAll(userId)` (les siennes). « seul un admin change le
  statut » → workflow que n'importe qui applique aux siennes. Build SUCCESS, review 100/100 →
  **app faussement parfaite**. Le miroir a raté le trou ET ajouté 2 non-problèmes (bruit).
- **coworking (complexe)** : rôles → fausses pages `/admin` sans garde + catalogue global (Space)
  sans owner → 8 erreurs tsc (`Space.userId`).

### La déclaration que l'ARCHITECT doit produire (nouveau : RoleDeclaration)
- `roles` : liste des rôles (ex: `["employee", "admin"]`)
- `privileged_role` : le rôle qui voit/gère tout (ex: `"admin"`)
- `admin_scoped_views` : entités/pages où l'admin voit TOUT (vs owner-scoped)
- `role_gated_actions` : actions exigeant le rôle privilégié (ex: transition de statut sur Request)
- `global_entities` : entités SANS owner (catalogue partagé, ex: Space)

### Les invariants (chacun : garantie déterministe OU check reviewer)
| # | Invariant | Garantie / Check | Statut |
|---|---|---|---|
| K1 | Le rôle est lu depuis **Clerk** (`sessionClaims.metadata.role`), jamais du client | helper déterministe | ❌ |
| K2 | Vue « admin voit tout » : `getAllAsAdmin()` **sans** filtre owner | service_modules (nouveau `admin`) | ❌ |
| K3 | Vue owner : reste filtrée par `userId` | crud.py (acquis A) | ✅ (hérité) |
| K4 | Action gardée par rôle : vérif **CÔTÉ SERVEUR** (pas juste l'UI cachée) | garde service/action + reviewer | ❌ |
| K5 | Page `/admin/*` : vérifie le rôle, redirige un non-admin | page generator + reviewer L1 | ❌ |
| K6 | Entité GLOBALE (sans owner) : **pas** de filtre `userId`, pas de `@@index([userId])` | service + model_context `ownerless` | ❌ (bug Space) |
| K7 | L'admin écrit/modifie des données d'AUTRUI (ex: statut d'une demande d'un autre) sans être bloqué par l'owner-guard | service admin-write | ❌ |
| K8 | Le SEED peuple des données de PLUSIEURS acteurs (sinon « admin voit tout » montre 1 seul) | dev_seed_generator | ❌ |

### Nettoyage LLM OBLIGATOIRE (prérequis — cause racine du bug)
> On ne peut PAS compiler les rôles si l'architect croit encore « tout a un userId, un seul acteur ».
> Le compilateur traduirait fidèlement une déclaration fausse.
- `domain_interpreter` `_DOMAIN_STACK_INVARIANTS` : « TOUS les modèles DOIVENT avoir userId » →
  **nuancer** : une entité peut être owned OU globale ; les rôles existent (ne plus aplatir).
- `brief_guide.md` règle 4 : « un seul acteur par app » → **réécrire** : un propriétaire de données,
  plusieurs niveaux d'accès (owner / privilégié).
- `rules_dev.md` : vérifier qu'aucune règle n'impose « toujours filtrer par userId » de façon absolue.

### FRANCHISE (transversal, mais critique ici)
- K9 | Le miroir (`unsupported[]`) doit **attraper le trou de rôle** quand la case n'existe pas encore,
  et **cesser de fabriquer** de fausses pages `/admin` vides. Mieux un trou déclaré qu'un décor à 100/100.

**« Type K terminé » = K1→K9 ✅ sur it-requests (rôle pur) ET coworking (rôle × catalogue global).**
Étalon double : it-requests doit distinguer admin/employé ; coworking doit builder ET tourner.
