# Plan — Prebuild Truth Engine
*Validé Claude + Codex — 30 Mars 2026*

---

## Modèle de coordination

```
Claude écrit le contrat  →  Codex implémente  →  Claude supervise + valide gate
```

**Règles de handoff :**
- Claude ne commence pas une supervision sans que Codex ait livré
- Codex ne commence pas une implémentation sans que le contrat Claude soit prêt
- Chaque gate est validée par Claude sur runs réels (sorties.md + logit.md)
- Si gate KO → Claude diagnostique, attribue fix ciblé à Codex ou le prend lui-même

**Légende des tâches :**
- `[C]` = Claude
- `[X]` = Codex
- `[C→X]` = Claude livre d'abord, Codex prend le relais
- `[GATE-C]` = Gate supervisée par Claude (bloquante)

---

## Séquence globale

```
Phase A          Phase B          Phase C          Phase D          Phase E
[C] contrats  →  [X] pipeline  →  [X] AST/ESLint →  [X] supprime  →  [C+X] holdout
[X] DEPRECATED   [C] classify  →  [C] RAG+JSON   →  [C] valide    →  [GATE-C] final
[GATE-C]         [GATE-C]         [GATE-C]           [GATE-C]
```

Phases A et B sont strictement séquentielles (B dépend des contrats A).
Au sein de chaque phase, certaines tâches sont parallélisables (indiqué ci-dessous).

---

## Objectif

Remplacer la logique de vérification maison (regex, substring, prompt-only) par les outils
natifs de la stack (tsc, eslint, prisma, tree-sitter). La factory devient un orchestrateur
fin sur une toolchain déterministe. Le LLM reçoit des violations structurées, pas du texte.

## Principe de transition

- Rien n'est supprimé avant que son remplacement soit prouvé en production.
- Les fichiers legacy passent en `DEPRECATED` d'abord, suppression seulement en Phase D.
- Chaque phase a une gate bloquante — si la gate ne passe pas, on ne passe pas à la suite.

---

## Phase A — Cadre + Observabilité (safe)

**Objectif** : poser les fondations sans toucher au flux actif.

### Étape A.1 — Claude en premier (Codex bloqué jusqu'ici)
*Parallélisable entre elles*

- `[C]` Écrire `schemas/prebuild_report.json`
  Structure : `stages[]` (tool, status, evidence, files, line/col),
  `violations[]` (rule_id, file, reason, fix_hint), `blocking`, `llm_correction_bundle`

- `[C]` Écrire le contrat d'interface `agents/prebuild_pipeline.py`
  Signatures exactes, inputs/outputs, ordre des 4 stages, docstrings — pas d'implémentation

- `[C]` Rédiger `PREBUILD_TOOL_MANIFEST.json`
  Chaque outil : nom, rôle, statut (planned/implemented/deprecated), remplace quoi

### Étape A.2 — Codex démarre après livraison A.1
*Parallélisable entre elles*

- `[X]` Confirmer le chemin actif (`dev_test_activity.py:568` → `run_dev_agent`)
  Documenter dans un commentaire inline les fichiers qui sont dead code

- `[X]` Marquer `DEPRECATED` (header + log WARNING au démarrage) :
  `agents/dev.py`, `agents/dev_loop.py`, `agents/pre_build_validator.py`,
  `agents/file_supervision_loop.py`, `agents/build_state_manager.py`

- `[X]` Marquer dans `nextjs-clerk-prisma.json` chaque content_guard :
  `"status": "legacy_ignored_by_dev_graph"` — pas supprimé

- `[X]` Vérifier 0 régression tests existants après marquage

### [GATE-C] Phase A
*Claude supervise sur résultats réels*
- `workflow_status=COMPLETED` >= 99% sur 3 runs post-marquage
- 0 régression tests existants (`pytest` vert)
- Schéma `prebuild_report.json` valide (jsonschema lint)
- Contrat interface approuvé par Claude avant que Codex commence Phase B

---

## Phase B — Pipeline Prébuild Minimal Branché

**Objectif** : exécuter les outils dans le bon ordre avant le build, produire le report.

### Étape B.1 — Codex implémente (sur base contrat A.1)
*Séquentiel : B.1a avant B.1b*

- `[X]` B.1a — Implémenter `agents/prebuild_pipeline.py` :
  `prisma validate` → `prisma generate` → `tsc --noEmit --format json` → `eslint --format json`
  Produit `prebuild_report.json` conforme au schéma Phase A
  Non-bloquant si un outil absent (log WARNING, continue)

- `[X]` B.1b — Câbler dans `dev_graph.py` :
  Appel après génération LLM, avant `npm run build`
  Si `blocking=true` → injecter `llm_correction_bundle` comme HumanMessage, pas de build

### Étape B.2 — Parallèle après B.1a livré

- `[X]` Câbler `journey_validator.py` dans `dev_test_activity.py`
  Remplace les métriques `user_flows_*` hardcodées à 0

- `[X]` Écrire `templates/.eslintrc.stack.json` minimal :
  Règles ESLint Next.js standard + `import/no-relative-packages`

- `[C]` Réécrire `_classify_root_cause()` :
  Lire sortie JSON de `tsc` et `eslint` depuis `prebuild_report.json`
  Remplace les 17 patterns substring — plus de text matching

- `[C]` Slim `dev_prompts.py` :
  Retirer toutes les règles couvertes par ESLint/TSC
  Garder : ordre de génération, fingerprint spec, savoir Clerk V6/Prisma 7 non-outillable
  Documenter dans `build_doctor.py` les cas runtime qu'il couvre encore (fallback)

### [GATE-C] Phase B
*Claude supervise sur 9 runs (3 batches)*
- `build_success >= 70%` sur 9 runs
- `root_cause_category=unknown` <= 10% sur runs failed
- `prebuild_report.json` produit sur 100% des runs
- 0 contradiction métrique
- Si gate KO → Claude diagnostique, fix ciblé attribué avant Phase C

---

## Phase C — Remplacements Robustes

**Objectif** : remplacer les dernières vérifications fragiles par des outils sémantiques.

### Étape C.1 — Codex implémente AST + ESLint avancé
*Parallélisable entre elles*

- `[X]` Implémenter guard AST `use_client` avec tree-sitter-typescript :
  Détecte import hook React sans `"use client"` comme premier statement AST
  Intégré dans `prebuild_pipeline.py` comme stage optionnel `ast_guards`
  Test : 0 faux positifs sur Server Components légitimes (layouts, API routes)

- `[X]` Enrichir `.eslintrc.stack.json` :
  `no-restricted-imports` Clerk (interdire `@clerk/nextjs` direct, forcer `/server`)
  `no-restricted-imports` Prisma relatif (forcer `@/lib/prisma`)

- `[X]` Ajouter config `dependency-cruiser` template :
  Frontières client/server, interdire imports server dans `app/` non-API

### Étape C.2 — Claude nettoie après C.1 livré
*Peut démarrer en parallèle de C.1 pour la partie RAG*

- `[C]` Déplacer vers Qdrant RAG (Zone 15+) le savoir non-outillable :
  Clerk V6 API, Prisma 7 defineConfig, PrismaPg adapter
  Retirer ces règles du prompt `dev_prompts.py`

- `[C]` Mettre à jour `nextjs-clerk-prisma.json` après confirmation C.1 :
  Supprimer `content_guards` (remplacés)
  Ajouter section `toolchain` avec ordre des stages

### [GATE-C] Phase C
*Claude supervise sur 9 runs*
- `build_success >= 80%` sur 9 runs
- Guard AST `use_client` : 0 faux positifs prouvés
- ESLint stack : 0 faux bloquants prouvés
- `tsc_errors_count` bloquants = 0 sur runs réussis

---

## Phase D — Nettoyage Final

**Objectif** : supprimer le code legacy prouvé inutile par les logs.

### Étape D.1 — Claude valide d'abord (avant toute suppression)

- `[C]` Analyser les 20 derniers runs :
  `build_doctor.py` appelé combien de fois ?
  `_classify_root_cause()` couvre-t-il encore des cas non-couverts par le parseur structuré ?
  Décision écrite : "supprimer" ou "garder fallback" pour chaque fichier

### Étape D.2 — Codex supprime sur décision Claude

- `[X]` Supprimer fichiers DEPRECATED confirmés inutiles :
  `agents/dev.py`, `agents/dev_loop.py`, `agents/pre_build_validator.py`,
  `agents/file_supervision_loop.py`, `agents/build_state_manager.py`
- `[X]` Supprimer `build_doctor.py` si décision Claude = "supprimer"
- `[X]` Nettoyer Dockerfile : retirer outils installés mais non câblés
- `[X]` Vérifier 0 import cassé dans le code actif après suppression

### Étape D.3 — Claude valide la cohérence finale

- `[C]` Vérifier `nextjs-clerk-prisma.json` : section `toolchain` propre, 0 `content_guards` orphelins
- `[C]` Mettre à jour `plan.md` : Phase 1 atteinte si gate Phase D verte

### [GATE-C] Phase D
*Claude supervise sur 6 runs post-nettoyage*
- Mêmes métriques Phase C (pas de régression)
- 0 référence aux fichiers supprimés dans le code actif
- `build_doctor.py` absent = pas de régression prouvée

---

## Phase E — Validation Anti-Overfit

**Objectif** : prouver que la stabilité est moteur-générique, pas brief-spécifique.

### Étape E.1 — Codex lance les runs

- `[X]` 3 runs briefs connus : task-manager, invoice-app, kanban-board
- `[X]` 3 runs briefs holdout (non utilisés pendant le développement) :
  personal-blog, expense-tracker, team-dashboard (ou équivalents du brief_catalog)

### Étape E.2 — Claude supervise et décide

- `[C]` Analyser sorties.md + logit.md des 6 runs
- `[C]` Comparer métriques briefs connus vs holdout
- `[C]` Décision Go/No-Go écrite sur chaque critère

### [GATE-C] Finale — Go/No-Go Phase 2 du plan.md
- `build_success >= 85%` sur holdout **uniquement**
- `spec_validation_status=OK` >= 95%
- `requirements_met/total >= 90%` moyen
- `root_cause=unknown` <= 5% sur runs failed
- 0 contradiction métrique
- 100% runs avec `prebuild_report.json`
- Si Go → Phase 2 du plan.md lancée (fenêtre 50 runs mixtes)

---

## Carte de suppression finale

| Fichier | Phase suppression | Condition |
|---|---|---|
| `agents/dev.py` | D | Gate C verte + 0 référence active |
| `agents/dev_loop.py` | D | idem |
| `agents/pre_build_validator.py` | D | ESLint + AST couvrent le même périmètre |
| `agents/build_state_manager.py` | D | idem |
| `agents/build_doctor.py` | D | Logs prouvent 0 utilité sur 20 runs |
| `content_guards` dans JSON | D | Après AST + ESLint câblés Phase C |
| `_classify_root_cause()` | D | Parseur structuré Phase B couvre tous les cas |
| ~40 règles dans dev_prompts | B+C | Au fur et à mesure du remplacement |

## Outils introduits

| Outil | Phase | Remplace |
|---|---|---|
| `tsc --noEmit --format json` | B | Substring error classification |
| `eslint --format json` | B | content_guards regex + prompt rules |
| `prisma validate` (déjà là) | B | Guard `prisma_schema_datasource_url` |
| `tree-sitter-typescript` | C | Guard `use_client` regex |
| `dependency-cruiser` | C | Path guards hardcodés |

## Multi-stack (après Phase E)

Chaque stack définit dans son JSON une section `toolchain` :
```json
{
  "toolchain": {
    "schema_check": "prisma validate",
    "schema_generate": "prisma generate",
    "type_check": "tsc --noEmit",
    "lint": "eslint --config .eslintrc.stack.json",
    "ast_guards": ["use_client"],
    "build": "next build"
  }
}
```
La factory orchestre la toolchain — elle ne connaît pas Next.js ou Django.
