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
