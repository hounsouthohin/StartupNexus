# PLAN DE REMODULARISATION — 17 Juillet 2026

> Objectif : laisser l'usine dans un **état sain** AVANT la Scène et avant l'expansion suivante,
> pour que chaque type suivant soit un **ajout** et non une chirurgie.
> Décision : **ce n'est PAS une réécriture — c'est une dé-duplication chirurgicale.**

---

## 1. CE QUI EST DÉJÀ SAIN (à ne pas toucher)

La chaîne de couches est celle d'un compilateur correct :

```
ARCHITECT (LLM)
   ↓
ProjectSpec (models, pages, enums) + EnrichedSpec (annotations, status_flows, features)   ← DÉCLARATIONS
   ↓
ModelGenerationContext (drapeaux par modèle : has_slug, status_flow, currency…)            ← AST par modèle
   ↓  lu par TOUS les générateurs (ordre réel dans dev_graph)
types → zod → services → actions → design → layout → pages → middleware → seo
      → page-clients → hub → feature_modules
   ↓
EXECUTOR LLM (les bords)  →  BUILD  →  quality_check (capteur)
```

**Preuve que c'est sain** : `status_flow` a été ajouté à `ModelGenerationContext` (16-17 Juil) et
**tout en a dérivé** sans toucher les générateurs un par un. `ModelGenerationContext` EST déjà la
source unique des faits par modèle. L'isolation `core/` (agnostique) vs `stacks/` (spécifique)
est prête pour le multi-stack.

---

## 2. LA MALADIE — une connaissance à QUATRE têtes

Quatre représentations parallèles du **même fait** (« quelles méthodes un service expose »),
dont **trois sont des miroirs recopiés à la main** :

| Représentation | Rôle | Nature |
|---|---|---|
| `service_modules/` (crud, child, public, relations, public_relations, slug, transition) | **génère le vrai `.ts`** | ✅ **LA VÉRITÉ** |
| `SERVICE_METHOD_REGISTRY` | validation spec_enricher + architect | 🔴 miroir main |
| `dev_service_spec.build_service_spec` → **CONTRACTS.md** | **ce que lit le LLM** | 🔴 miroir main |
| `build_factory_capabilities_string` | prompt architect | 🔴 texte main |

**Preuve** : `getPublished` a vécu dans les quatre → méthode fantôme → TS2339.
Son docstring l'avoue : *« Miroir AUTORITAIRE… l'ajouter ici AUSSI »*. « Aussi » = la dérive.

**Bug latent lié (D33)** : le registre sur-liste `getBySlugWithRelations` sous `if_slug` seul,
alors que `slug.py:64` ne l'émet que si `has_slug ET relations`.

### Dettes annexes
- **2 copies du générateur d'actions** (`_generate_actions_for_model` + `_actions_block` collision).
- **Connaissance éparpillée dans les prompts** (architect.py inline, dev_prompts.py,
  dev_system_prompt.j2, rules_dev.md, factory_capabilities.md, RAG) — dont une partie **décrit du
  code déterministe que le LLM n'écrit plus** (D21/DY3).

---

## 3. LE PRINCIPE CIBLE

> **Pour chaque type de connaissance : UNE source ; tout le reste en DÉRIVE.**

Appliqué : **le module qui ÉMET une méthode DÉCLARE cette méthode (nom + signature), à côté du
code qui la génère.** Diverger devient structurellement impossible.

```python
class ServiceMethodModule(ABC):
    def should_activate(self, ctx) -> bool: ...
    def generate(self, ctx, **kwargs) -> list[str]: ...   # le code TS
    def methods_for(self, ctx) -> list[MethodDecl]: ...   # nom + signature — MÊME fichier
```
→ `methods_for_ctx(ctx)` parcourt les modules actifs et agrège.
→ CONTRACTS.md, le registre et les capabilities **dérivent** de cette source unique.

**Effet de bord gratuit** : D33 disparaît — `slug.py` déclare `getBySlugWithRelations`
uniquement quand il l'émet réellement.

---

## 4. MIGRATION — en étapes validées (jamais de big-bang)

| Étape | Contenu | Statut |
|---|---|---|
| **A** | `MethodDecl` + `methods_for()` sur les 7 modules + `methods_for_ctx()` | ✅ **17 Juil** |
| **B** | `build_service_spec` **dérive** → miroir CONTRACTS.md tué (90 lignes) | ✅ validé par run |
| **C** | `SERVICE_METHOD_REGISTRY` **supprimé** ; `valid_methods_for_flags` + capabilities **dérivés** via contexte minimal | ✅ validé |
| **D** | 2 copies du générateur d'actions **fusionnées** (133 lignes) | ✅ validé (`COMPLETED`/`SUCCESS`) |
| **E** | Élaguer les prompts décrivant du code déterministe (D21/DY3) | ⏸️ **reporté — valeur retombée** |

### Bilan A→D : 3 bugs latents corrigés SANS les chercher
Chaque suppression de copie a fait disparaître un mensonge :
1. **D33** — le registre annonçait `getBySlugWithRelations` dès qu'il y a un slug (au lieu de slug **ET** relations).
2. **Signature `getAll`** — la doc oubliait `pageSize` (le vrai code émet `page=1, pageSize=20`).
3. **TS2304 latent** — la copie « collision » du générateur d'actions n'avait pas le correctif `is_child` :
   `revalidatePath(...validated.parentId)` après le `catch` → `validated` hors scope. Toute app à
   modèles enfants avec collision de page aurait cassé au build.

**Une doc qui DÉRIVE du code ne peut plus mentir.** C'est la preuve empirique du principe.

### Pourquoi E est reporté (décision 17 Juil)
E devait alléger le prompt du **dev executor**. Or l'executor écrit désormais **0 fichier** sur une
app type A/D/I (constaté notes-frais : `[executor] plan vide — tout pré-généré`). Nettoyer un prompt
quasi inutilisé est devenu du polish : la valeur de E a chuté avec la couverture des compilateurs.
À reprendre si/quand la part LLM remonte.

**Règle** : chaque étape se valide par un **run + lecture du code généré**, jamais par une métrique.

---

## 5. CE QUI N'EST PAS DANS CE PLAN (volontairement)

- **Pas de réécriture des couches** — elles sont saines.
- **Pas de refonte des générateurs** — ils lisent déjà `ModelGenerationContext`.
- **Pas d'extension du RAG** — gelé (voir roadmap v4.0 §3).

---

## 6. APRÈS

État sain → **Scène** (A: miroir français, B: aperçu peuplé) → **expansion suivante (type K)**
où l'on modifiera peu et gagnera quand même. C'est l'ordre décidé le 17 Juil.
