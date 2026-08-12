"""
dev_oracle_generator.py — ORACLES dérivés de la déclaration (le « 5ᵉ lot »).
────────────────────────────────────────────────────────────────────────────
Trouvaille : « une intention sans case s'évapore ; une case sans oracle est une case
non vérifiée. » Chaque case doit émettre DEUX moitiés — un compilateur (le code) ET un
générateur d'oracle (sa preuve). Ce fichier pose la première : le type I (machine à états).

Depuis `status_flows`, la liste BLANCHE des transitions donne, par complément, la matrice
des transitions INTERDITES. L'oracle affirme, contre l'app QUI TOURNE (la Scène) : toute
transition interdite depuis l'état courant d'un enregistrement seedé doit être REFUSÉE.

Ce n'est pas un compilateur (ça juge le SENS), pas un LLM (ça ne peut pas complimenter) :
ça passe ou ça échoue, et la vérité de référence est la déclaration elle-même.

Sortie : `app/api/_oracle/route.ts` — dev-only (actif si ORACLE_ENABLED=1, sinon { skipped }).
Un lanceur (le worker) frappe /api/_oracle une fois le preview lancé → pass/fail.
"""
from __future__ import annotations

import json
import logging
import os

logger = logging.getLogger(__name__)


def _statusflow_block(ctx) -> list[str] | None:
    """Bloc d'assertions pour UN modèle à machine à états (type I). None sinon."""
    flow = getattr(ctx, "status_flow", None)
    if flow is None:
        return None
    name = ctx.name
    camel = ctx.camel
    transitions = dict(getattr(flow, "transitions", {}) or {})
    if not transitions:
        return None
    all_states = list(transitions.keys())
    _trans = json.dumps(transitions, ensure_ascii=False)
    _states = json.dumps(all_states, ensure_ascii=False)
    return [
        f"  // ── type I — {name} : les transitions INTERDITES doivent être refusées ──",
        "  {",
        f"    const transitions: Record<string, string[]> = {_trans}",
        f"    const allStates: string[] = {_states}",
        f"    const items = (await {camel}Service.getAll(OWNER)) as Array<{{ id: string; status: string }}>",
        "    const rec = items[0]",
        "    if (!rec) {",
        f"      checks.push({{ entite: '{name}', assertion: 'donnee de test presente', ok: false, note: 'aucun enregistrement seede pour OWNER' }})",
        "    } else {",
        "      const allowed = transitions[rec.status] ?? []",
        "      const forbidden = allStates.filter((t) => !allowed.includes(t) && t !== rec.status)",
        "      for (const target of forbidden) {",
        f"        const refused = await assertThrows(() => {camel}Service.transitionTo(OWNER, rec.id, target))",
        f"        checks.push({{ entite: '{name}', assertion: `transition ${{rec.status}} -> ${{target}} refusee`, ok: refused, note: refused ? undefined : 'transition interdite ACCEPTEE' }})",
        "      }",
        "    }",
        "  }",
    ]


def generate_oracle_file(spec, project_workdir: str, contexts: dict | None = None) -> dict[str, str]:
    """Écrit app/api/_oracle/route.ts si au moins un modèle a une machine à états.
    Retourne {rel_path: content} pour template_written (le LLM ne l'écrase pas)."""
    if not contexts:
        return {}

    blocks: list[list[str]] = []
    imports: list[str] = []
    for _name, ctx in contexts.items():
        blk = _statusflow_block(ctx)
        if blk:
            blocks.append(blk)
            imports.append(f"import {{ {ctx.camel}Service }} from '@/lib/services/{ctx.kebab}.service'")

    if not blocks:
        return {}

    lines: list[str] = [
        "// AUTO-GÉNÉRÉ PAR dev_oracle_generator.py — ORACLE (dev only, ne pas modifier).",
        "// Preuves dérivées de la déclaration, exécutées contre l'app qui tourne.",
        "// Actif uniquement si ORACLE_ENABLED=1 (sinon renvoie { skipped: true }).",
        "import { NextResponse } from 'next/server'",
        *imports,
        "",
        "export const dynamic = 'force-dynamic'",
        "const OWNER = process.env.SEED_USER_ID ?? 'user_demo'",
        "",
        "type Check = { entite: string; assertion: string; ok: boolean; note?: string }",
        "",
        "async function assertThrows(fn: () => Promise<unknown>): Promise<boolean> {",
        "  try { await fn(); return false } catch { return true }",
        "}",
        "",
        "export async function GET() {",
        "  if (process.env.ORACLE_ENABLED !== '1') return NextResponse.json({ skipped: true })",
        "  const checks: Check[] = []",
        "",
    ]
    for blk in blocks:
        lines += blk
        lines.append("")
    lines += [
        "  const passed = checks.every((c) => c.ok)",
        "  return NextResponse.json(",
        "    { passed, total: checks.length, failed: checks.filter((c) => !c.ok).length, checks },",
        "    { status: passed ? 200 : 500 },",
        "  )",
        "}",
        "",
    ]
    content = "\n".join(lines)

    # NB : PAS de préfixe underscore — Next.js traite `_dossier` comme un dossier PRIVÉ,
    # exclu du routage (→ 404). Donc `oracle`, pas `_oracle`.
    rel_path = "app/api/oracle/route.ts"
    abs_dir = os.path.join(project_workdir, "app", "api", "oracle")
    os.makedirs(abs_dir, exist_ok=True)
    try:
        with open(os.path.join(abs_dir, "route.ts"), "w", encoding="utf-8") as f:
            f.write(content)
        logger.info("[oracle_gen] ✓ app/api/_oracle/route.ts généré (%d case(s) à machine à états)", len(blocks))
    except Exception as e:
        logger.error("[oracle_gen] ✗ Erreur écriture oracle : %s", e)
        return {}

    return {rel_path: content}
