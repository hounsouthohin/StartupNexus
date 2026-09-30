# 04 — Générateurs de la couche données (déterministes, protégés)

Tous produisent du TypeScript par CONCATÉNATION DE CHAÎNES Python (pas de templates ici), lisent le ModelGenerationContext, écrivent sur disque et sont enregistrés dans `template_written` (le LLM ne peut pas les réécrire).

| Générateur | Produit | Logique clé |
|---|---|---|
| `dev_types_generator` | `lib/types.ts` | Re-export types/enums Prisma ; `CreateXxxInput = Omit<Prisma.XxxUncheckedCreateInput, auto+owner+slug+m2m> & {tagIds?}` ; `UpdateXxxInput = Partial` ; `SerializedXxx` explicite (DateTime→string, owner exclu, relations en inline optionnel 1 niveau) ; types de params de route. |
| `dev_zod_generator` | `lib/schemas.ts` | Create/Update schemas depuis editable_fields − create_excluded_fields ; raffinement sémantique (email/url/nombre ≥0 par NOM de champ puis annotation) ; **réexporte un 2e `CreateXxxInput = z.infer<…>` (collision avec types.ts)**. |
| `dev_service_generator` + `service_modules/*` | `lib/services/<m>.service.ts` | `_serialize` + assemblage des modules actifs + required_queries compilées (filter_by_field, search_text, count_by_field, filter_by_relation). |
| `dev_actions_generator` | `app/<liste>/actions.ts` + `lib/auth-role.ts` | create/update/delete (+ transition si workflow) ; Zod parse du FormData (getAll pour M2M) ; redirect/revalidate vers la liste (ou page détail parent pour un enfant) ; gardes K4 (`requireRole` si verbe gardé) et S1 (initiateur) ; `auth-role.ts` = rôle depuis Clerk (ADMIN_EMAILS bootstrap + publicMetadata.role). Fusion si 2 modèles partagent la même liste. |
| `dev_seed_generator` | `prisma/seed.mjs` | 2 lignes/modèle, ordre topologique FK, état initial du workflow, 1re valeur d'enum, valeurs par nom de champ, 2 owners si multi-acteur, rien pour les globales. |
| `dev_oracle_generator` | `app/api/oracle/route.ts` | Seulement workflow : teste que les transitions interdites sont refusées. Jamais appelé. |
| `dev_prisma_extractor` | (prompt LLM) | Lit le DMMF réel de @prisma/client via Node → carte des types pour l'executor. |

## Services — détails importants
- CRUD : getAll/getById/create/update/delete filtrés par owner ; `is_global` retire l'owner (SEULEMENT dans crud.py) ; getAllAsAdmin/getByIdAsAdmin si admin-scoped ; garde FK d'appartenance (S6) ; M2M pré-filtré par owner (S10) ; slug auto + anti-collision ; état initial forcé ; garde de transition + verrou dans update.
- Relations / Child / Slug(getBySlugOwned) : `where {owner}` écrit EN DUR → ignorent `is_global` (bug atelier).
- Public / Slug / PublicRelations : même recherche de « champ de visibilité » recopiée 3 fois ; getPublicAll sur modèle à statut filtre sur une valeur « published-like » sinon la 1re valeur de l'enum ; filtre date future par nom de champ (date, startDate…).
- Transition : `transitionTo` écrit statut + state_fields de l'état cible ; lève le filtre owner si la transition est gardée par rôle.
- Partout : pagination 20 par défaut, tri `createdAt desc` en dur, relations sur 1 niveau.

## Rôles — logique codée pour EXACTEMENT 2 acteurs
Garde d'initiateur : « si initiateur = privilégié → requireRole, sinon → interdire au privilégié ». Update/delete non gardés hors `gated_verbs` (le propriétaire peut supprimer sa demande même après décision ; le verrou ne couvre pas delete).

## Lecture conception
Chaque concept (owner, global, visibilité, rôle, workflow) est ré-écrit dans plusieurs modules par copie de motifs de chaînes. C'est exactement là que naissent les divergences observées (types vs zod, crud vs relations). Une matrice des capacités + des helpers uniques (clause where, champ de visibilité, garde de rôle) supprimerait ces copies.
