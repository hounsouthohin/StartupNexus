# R2 — Architecture "Synthèse sous Contraintes"
## Scaffold Déterministe + File-Level Gate + FileMap Enrichi

> Auteur : conception collaborative Claude + utilisateur — 16 Avril 2026  
> Statut : DESIGN VALIDÉ — prêt pour implémentation  
> Prérequis : R1 appliqué (GraphRecursionError fix + threshold 0.25)

---

## Problème résolu

La génération libre ("écris tout puis valide") plafonne à ~65-70% de build success.
Cause : le LLM choisit librement les imports → conflits de types non détectés avant `npm run build`.

Solution : le LLM ne touche plus aux imports ni aux signatures. Il remplit uniquement des corps.

---

## Nouveau graph LangGraph

```
START
  │
  ▼
[scaffold_node]           ← Python pur — génère squelettes depuis IR Architect
  │ Écrit chaque fichier avec zones de remplacement marquées
  ▼
┌─────────────────────────────────────────┐
│  BOUCLE PAR FICHIER (files_queue)       │
│                                         │
│  [dev_node]                             │
│    LLM reçoit 1 fichier avec zones      │
│    Interdit : toucher imports/signatures │
│    Autorisé : imports depuis whitelist  │
│    Remplace [[LLM_IMPORTS_ZONE]]        │
│    Remplace [[LLM_LOGIC_ZONE]]          │
│       │                                 │
│  [file_tsc_gate]                        │
│    tsc --noEmit <fichier> seulement     │
│    OK  → types_exported → FileMap       │
│    ERR → retour dev_node (max 2 retry)  │
│       │                                 │
│  next file? → loop                      │
└─────────────────────────────────────────┘
  │ Tous les fichiers validés
  ▼
[build_node]
  npm run build (global)
  │
  ▼
END
```

---

## DevState étendu

```python
class DevState(TypedDict):
    # ... champs existants ...

    # R2 — Scaffold
    scaffold_done: bool          # True une fois scaffold_node exécuté
    files_queue: List[str]       # Fichiers restants à remplir (dans l'ordre IR)
    current_file: str            # Fichier en cours de traitement LLM
    file_retries: int            # Tentatives sur le fichier courant (max 2)

    # R2 — FileMap enrichi (suggestion utilisateur 3)
    filemap: dict
    # Structure :
    # {
    #   "lib/api-helpers.ts": {
    #     "status": "validated",          # "pending" | "validated" | "failed"
    #     "types_exported": [             # Signatures réelles extraites après tsc OK
    #       "formatCurrency(val: number): string",
    #       "formatDate(d: Date): string"
    #     ],
    #     "imports_used": ["import { format } from 'date-fns'"]
    #   },
    #   "app/page.tsx": { "status": "pending", ... }
    # }
```

---

## Zones de remplacement (suggestion utilisateur 2)

Chaque fichier scaffoldé contient des marqueurs explicites :

```typescript
// ── GÉNÉRÉ PAR SCAFFOLD — NE PAS MODIFIER CE BLOC ──────────────────
import { auth } from '@clerk/nextjs/server'
import { NextResponse } from 'next/server'
import { prisma } from '@/lib/prisma'
import { Post } from '@prisma/client'
// ────────────────────────────────────────────────────────────────────

/* [[LLM_IMPORTS_ZONE]] */
// Ajoute ici UNIQUEMENT des imports depuis la whitelist (voir ci-dessous).
// Ne modifie PAS les imports au-dessus.

export async function GET(req: Request) {
  /* [[LLM_LOGIC_ZONE]] */
}
```

**Deux zones distinctes :**
- `[[LLM_IMPORTS_ZONE]]` : imports utilitaires métier depuis la whitelist
- `[[LLM_LOGIC_ZONE]]` : corps de la fonction uniquement

---

## Whitelist d'imports LLM (suggestion utilisateur 1 — Import Paradox)

Résout le problème : "LLM veut utiliser `date-fns` mais n'a pas le droit d'écrire les imports".

La whitelist est dérivée des `packages` + `dev_packages` du JSON stack :

```python
# agents/dev_scaffold.py
IMPORT_WHITELIST = {
    # Extraits de nextjs-clerk-prisma.json → packages + dev_packages
    "zod":          "import { z } from 'zod'",
    "date-fns":     None,   # pas dans packages → INTERDIT
    "lodash":       None,   # pas dans packages → INTERDIT
    "clsx":         None,   # pas dans packages → INTERDIT
    # Autorisés :
    "react":        "import React from 'react'",
    "next/navigation": "import { useRouter, redirect } from 'next/navigation'",
    "next/headers": "import { cookies, headers } from 'next/headers'",
    "@clerk/nextjs/server": "import { auth, currentUser } from '@clerk/nextjs/server'",
    "@prisma/client": "import { Prisma } from '@prisma/client'",
    # Types Prisma générés :
    "prisma-types": "import type { {ModelName} } from '@prisma/client'",
}
```

**Prompt LLM — section imports :**
```
Tu PEUX ajouter des imports dans [[LLM_IMPORTS_ZONE]] UNIQUEMENT si la librairie
est dans cette liste : {whitelist_names}.
Si tu as besoin d'une fonction non listée, implémente-la inline.
```

---

## Context Injection (suggestion utilisateur 3 — FileMap enrichi)

Avant chaque appel LLM sur `current_file`, injecter le résumé du FileMap :

```python
def build_filemap_context(filemap: dict, current_file: str) -> str:
    """
    Génère le contexte des fichiers déjà validés pour le LLM.
    Le LLM sait exactement ce qui est disponible avant d'écrire.
    """
    lines = ["## Fichiers déjà validés (disponibles à l'import)\n"]
    for path, info in filemap.items():
        if info.get("status") != "validated":
            continue
        if path == current_file:
            continue
        sigs = info.get("types_exported", [])
        if sigs:
            lines.append(f"### `{path}`")
            for sig in sigs:
                lines.append(f"  - `{sig}`")
    return "\n".join(lines) if len(lines) > 1 else ""
```

**Exemple de contexte injecté pour `app/page.tsx` :**
```
## Fichiers déjà validés (disponibles à l'import)

### `lib/api-helpers.ts`
  - `formatCurrency(val: number): string`
  - `formatDate(d: Date): string`

### `app/api/posts/route.ts`
  - `GET(): Promise<NextResponse>`
  - `POST(req: Request): Promise<NextResponse>`
```

---

## Extraction des types exportés après tsc OK

```python
import re

def extract_exports(file_content: str) -> list[str]:
    """
    Extrait les signatures exportées depuis un fichier TypeScript validé.
    Utilisé pour enrichir le FileMap après file_tsc_gate OK.
    """
    patterns = [
        r"export\s+(?:async\s+)?function\s+(\w+\([^)]*\)(?:\s*:\s*\S+)?)",
        r"export\s+(?:const|let)\s+(\w+\s*:\s*[^=\n]+)",
        r"export\s+(?:type|interface)\s+(\w+(?:<[^>]+>)?(?:\s*\{[^}]+\})?)",
        r"export\s+default\s+(?:async\s+)?function\s+(\w+\([^)]*\)(?:\s*:\s*\S+)?)",
    ]
    found = []
    for p in patterns:
        found.extend(re.findall(p, file_content))
    return found[:10]  # Cap à 10 pour ne pas surcharger le contexte
```

---

## Ordre de génération des fichiers

L'ordre est critique : générer les fichiers feuilles avant les fichiers qui en dépendent.

```python
FILE_GENERATION_ORDER = [
    # 1. Types et utilitaires (aucune dépendance interne)
    "lib/types.ts",
    "lib/utils.ts",
    "lib/api-helpers.ts",
    # 2. Routes API (dépend de prisma + clerk — déjà dans imports déterministes)
    "app/api/*/route.ts",
    # 3. Server Components (dépend des routes)
    "app/*/page.tsx",
    # 4. Client Components (dépend des server components)
    "components/*.tsx",
]
```

L'Architect IR détermine l'ordre réel via `ir_schema.generation_order[]`.

---

## Ce qui NE CHANGE PAS (réutilisé tel quel)

| Composant | Raison |
|---|---|
| `prebuild_pipeline.py` | Devient le `file_tsc_gate` (même code, scope réduit à 1 fichier) |
| `write_template_files()` | Toujours exécuté avant scaffold (14 fichiers infrastructure) |
| `ProjectSpec.to_prisma_schema_block()` | Déterministe, conservé |
| `_prune_messages()` | Toujours pertinent pour la boucle de retry par fichier |
| `MAX_BUILD_ATTEMPTS` | Renommé `MAX_FILE_RETRIES = 2` pour la boucle fichier |

---

## Modifications Architect IR nécessaires

Ajouter dans le prompt `spec_writer` de `architect.py` :

```
Pour chaque fichier dans pages[] et routes[] :
- "imports_required": liste d'imports déterministes (clerk, prisma, next)
- "types_needed": ["Post", "User"] — types Prisma ou internes requis
- "return_type": "Promise<NextResponse>" pour les routes
- "llm_hint": indication courte sur la logique métier à implémenter

Pour chaque modèle dans models[] :
- "relationships": explicitées (relation Prisma exacte)

Génère aussi :
- "generation_order": ordre de création des fichiers (feuilles d'abord)
```

---

## Implémentation — Fichiers à créer / modifier

| Fichier | Action | Priorité |
|---|---|---|
| `agents/dev_scaffold.py` | **CRÉER** — scaffold_node + zones + whitelist | R2-A |
| `agents/dev_graph.py` | **MODIFIER** — DevState + graph nodes + filemap | R2-B |
| `agents/dev_scaffold_types.py` | **CRÉER** — extract_exports() + build_filemap_context() | R2-C |
| `agents/architect.py` | **MODIFIER** — enrichir IR avec imports_required + generation_order | R2-D |
| `config/stacks/nextjs-clerk-prisma.json` | **MODIFIER** — ajouter "import_whitelist" section | R2-E |
