"""
dev_page_composer.py — Couche B FrontendActivity (Sprint 4.9A)

Rewrite LLM file-by-file des page-client.tsx pour utiliser les composants du Design System.
Stratégie : un appel LLM par fichier → isolation totale → pas de pollution de contexte.
Si le LLM échoue ou produit un résultat vide : fichier original conservé (silently).
"""
from __future__ import annotations

import os
import pathlib
import re
from typing import Dict, List, Optional

from openai import OpenAI

_client: Optional[OpenAI] = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    return _client


# ─────────────────────────────────────────────────────────────────────────────
# Prompt
# ─────────────────────────────────────────────────────────────────────────────

_SYSTEM_PROMPT = """\
You are a senior Next.js UI developer. Your task is to rewrite a page-client.tsx file \
to use pre-built design system components.

AVAILABLE DESIGN SYSTEM COMPONENTS (import from "@/app/components/ui"):
- Button: props variant ("primary"|"secondary"|"danger"|"ghost"), size ("sm"|"md"|"lg"), \
loading (bool), disabled (bool) + all standard button HTML attributes
- Card: props title? (string), description? (string), children, footer? (ReactNode), className?
- Table<T extends {id:string}>: props columns ({key, label, render?}[]), rows (T[]), \
emptyMessage?, actions? ((row:T)=>ReactNode)
- Badge: props variant ("success"|"warning"|"danger"|"info"|"neutral"), children
- Empty: props title (string), description? (string), action? (ReactNode), className?
- StatCard: props label (string), value (string|number), trend? (string), \
trendDirection? ("up"|"down"|"flat"), className?

RULES (MANDATORY):
1. Keep 'use client' directive at the top
2. Keep ALL existing imports (Link, useRouter, useState, actions, types — do NOT remove any)
3. Add a single import line for needed UI components: import { Button, Card, ... } from "@/app/components/ui"
4. Replace raw <button> elements with <Button> component
5. Replace raw table+thead+tbody patterns with <Table> component
6. Replace status <span> elements with <Badge> component
7. Wrap page sections in <Card> when appropriate (avoid deep nesting)
8. Replace empty-state divs with <Empty> component
9. Replace stat/metric divs with <StatCard> component
10. Keep ALL business logic unchanged: server actions calls, service calls, data props, types
11. Keep ALL routing logic unchanged: Link hrefs, router.push, redirects
12. Output ONLY the TypeScript/TSX code — no explanation, no markdown fences

If the file is too complex or risky to rewrite cleanly, output the ORIGINAL FILE UNCHANGED."""

_USER_TEMPLATE = """\
Rewrite this page-client.tsx to use the design system components:

```tsx
{content}
```"""


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

_FENCE_RE = re.compile(r"^```(?:tsx?|jsx?)?\n?(.*?)(?:\n?```)?$", re.DOTALL)


def _strip_fences(text: str) -> str:
    m = _FENCE_RE.match(text.strip())
    return m.group(1).strip() if m else text.strip()


def _looks_valid(content: str) -> bool:
    """Sanity check : le résultat est-il du TSX plausible ?"""
    stripped = content.strip()
    if not stripped:
        return False
    if "'use client'" not in stripped and '"use client"' not in stripped:
        return False
    if "export default" not in stripped and "export function" not in stripped:
        return False
    return True


def _find_page_client_files(project_workdir: str) -> List[str]:
    """Retourne les chemins relatifs de tous les page-client.tsx."""
    base = pathlib.Path(project_workdir)
    results: List[str] = []
    for p in base.rglob("page-client.tsx"):
        rel = p.relative_to(base).as_posix()
        # Exclure les composants du design system lui-même
        if "components/ui" not in rel:
            results.append(rel)
    return sorted(results)


# ─────────────────────────────────────────────────────────────────────────────
# Entrée publique
# ─────────────────────────────────────────────────────────────────────────────

def compose_pages(project_workdir: str) -> Dict[str, str]:
    """
    Rewrite LLM file-by-file.
    Retourne {rel_path: new_content} pour les fichiers effectivement modifiés.
    Les fichiers que le LLM n'améliore pas (ou dont la réécriture échoue) sont exclus.
    """
    base = pathlib.Path(project_workdir)
    target_files = _find_page_client_files(project_workdir)
    updated: Dict[str, str] = {}

    if not target_files:
        return updated

    llm = _get_client()

    for rel_path in target_files:
        abs_path = base / rel_path
        try:
            original = abs_path.read_text(encoding="utf-8")
        except Exception:
            continue

        try:
            response = llm.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": _USER_TEMPLATE.format(content=original)},
                ],
                temperature=0.1,
                max_tokens=4096,
            )
            raw = response.choices[0].message.content or ""
            rewritten = _strip_fences(raw)
        except Exception:
            continue

        if not _looks_valid(rewritten):
            continue

        # Si le LLM a retourné le fichier original inchangé → skip (pas de write inutile)
        if rewritten == original.strip():
            continue

        abs_path.write_text(rewritten, encoding="utf-8")
        updated[rel_path] = rewritten

    return updated
