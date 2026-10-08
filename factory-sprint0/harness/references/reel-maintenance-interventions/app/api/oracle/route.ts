// AUTO-GÉNÉRÉ PAR dev_oracle_generator.py — ORACLE (dev only, ne pas modifier).
// Preuves dérivées de la déclaration, exécutées contre l'app qui tourne.
// Actif uniquement si ORACLE_ENABLED=1 (sinon renvoie { skipped: true }).
import { NextResponse } from 'next/server'
import { interventionService } from '@/lib/services/intervention.service'

export const dynamic = 'force-dynamic'
const OWNER = process.env.SEED_USER_ID ?? 'user_demo'

type Check = { entite: string; assertion: string; ok: boolean; note?: string }

async function assertThrows(fn: () => Promise<unknown>): Promise<boolean> {
  try { await fn(); return false } catch { return true }
}

export async function GET() {
  if (process.env.ORACLE_ENABLED !== '1') return NextResponse.json({ skipped: true })
  const checks: Check[] = []

  // ── type I — Intervention : les transitions INTERDITES doivent être refusées ──
  {
    const transitions: Record<string, string[]> = {"planned": ["confirmed", "cancelled"], "confirmed": ["completed", "cancelled"], "completed": [], "cancelled": []}
    const allStates: string[] = ["planned", "confirmed", "completed", "cancelled"]
    const items = (await interventionService.getAll(OWNER)) as Array<{ id: string; status: string }>
    const rec = items[0]
    if (!rec) {
      checks.push({ entite: 'Intervention', assertion: 'donnee de test presente', ok: false, note: 'aucun enregistrement seede pour OWNER' })
    } else {
      const allowed = transitions[rec.status] ?? []
      const forbidden = allStates.filter((t) => !allowed.includes(t) && t !== rec.status)
      for (const target of forbidden) {
        const refused = await assertThrows(() => interventionService.transitionTo(OWNER, rec.id, target))
        checks.push({ entite: 'Intervention', assertion: `transition ${rec.status} -> ${target} refusee`, ok: refused, note: refused ? undefined : 'transition interdite ACCEPTEE' })
      }
    }
  }

  const passed = checks.every((c) => c.ok)
  return NextResponse.json(
    { passed, total: checks.length, failed: checks.filter((c) => !c.ok).length, checks },
    { status: passed ? 200 : 500 },
  )
}
