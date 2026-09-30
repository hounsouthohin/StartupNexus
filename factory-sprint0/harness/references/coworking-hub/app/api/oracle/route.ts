// AUTO-GÉNÉRÉ PAR dev_oracle_generator.py — ORACLE (dev only, ne pas modifier).
// Preuves dérivées de la déclaration, exécutées contre l'app qui tourne.
// Actif uniquement si ORACLE_ENABLED=1 (sinon renvoie { skipped: true }).
import { NextResponse } from 'next/server'
import { reservationService } from '@/lib/services/reservation.service'
import { invoiceService } from '@/lib/services/invoice.service'

export const dynamic = 'force-dynamic'
const OWNER = process.env.SEED_USER_ID ?? 'user_demo'

type Check = { entite: string; assertion: string; ok: boolean; note?: string }

async function assertThrows(fn: () => Promise<unknown>): Promise<boolean> {
  try { await fn(); return false } catch { return true }
}

export async function GET() {
  if (process.env.ORACLE_ENABLED !== '1') return NextResponse.json({ skipped: true })
  const checks: Check[] = []

  // ── type I — Reservation : les transitions INTERDITES doivent être refusées ──
  {
    const transitions: Record<string, string[]> = {"requested": ["confirmed", "refused"], "confirmed": ["completed", "cancelled"], "refused": [], "completed": [], "cancelled": []}
    const allStates: string[] = ["requested", "confirmed", "refused", "completed", "cancelled"]
    const items = (await reservationService.getAll(OWNER)) as Array<{ id: string; status: string }>
    const rec = items[0]
    if (!rec) {
      checks.push({ entite: 'Reservation', assertion: 'donnee de test presente', ok: false, note: 'aucun enregistrement seede pour OWNER' })
    } else {
      const allowed = transitions[rec.status] ?? []
      const forbidden = allStates.filter((t) => !allowed.includes(t) && t !== rec.status)
      for (const target of forbidden) {
        const refused = await assertThrows(() => reservationService.transitionTo(OWNER, rec.id, target))
        checks.push({ entite: 'Reservation', assertion: `transition ${rec.status} -> ${target} refusee`, ok: refused, note: refused ? undefined : 'transition interdite ACCEPTEE' })
      }
    }
  }

  // ── type I — Invoice : les transitions INTERDITES doivent être refusées ──
  {
    const transitions: Record<string, string[]> = {"pending": ["paid", "overdue"], "paid": [], "overdue": []}
    const allStates: string[] = ["pending", "paid", "overdue"]
    const items = (await invoiceService.getAll(OWNER)) as Array<{ id: string; status: string }>
    const rec = items[0]
    if (!rec) {
      checks.push({ entite: 'Invoice', assertion: 'donnee de test presente', ok: false, note: 'aucun enregistrement seede pour OWNER' })
    } else {
      const allowed = transitions[rec.status] ?? []
      const forbidden = allStates.filter((t) => !allowed.includes(t) && t !== rec.status)
      for (const target of forbidden) {
        const refused = await assertThrows(() => invoiceService.transitionTo(OWNER, rec.id, target))
        checks.push({ entite: 'Invoice', assertion: `transition ${rec.status} -> ${target} refusee`, ok: refused, note: refused ? undefined : 'transition interdite ACCEPTEE' })
      }
    }
  }

  const passed = checks.every((c) => c.ok)
  return NextResponse.json(
    { passed, total: checks.length, failed: checks.filter((c) => !c.ok).length, checks },
    { status: passed ? 200 : 500 },
  )
}
