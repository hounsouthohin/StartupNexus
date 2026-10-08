'use client'

import { useActionState } from 'react'
import Link from 'next/link'
import type { SerializedIntervention } from '@/lib/types'
import type { SerializedClient } from '@/lib/types'
import type { SerializedTechnician } from '@/lib/types'
import { updateIntervention } from '@/app/interventions/actions'

// Verrou d'édition (type I) : dans ces états les champs métier sont figés. Le changement
// d'état lui-même se fait via les boutons de transition de la page détail, pas ici.
const FLOW_LOCKED: string[] = ["cancelled", "completed"]

interface InterventionEditClientProps {
  item: SerializedIntervention
  clientOptions: SerializedClient[]
  technicianOptions: SerializedTechnician[]
}

export default function InterventionEditClient({ item, clientOptions, technicianOptions }: InterventionEditClientProps) {
  const [error, formAction, isPending] = useActionState(
    async (_prev: unknown, formData: FormData) => {
      try { await updateIntervention.bind(null, item.id)(formData); return null }
      catch (e) { return (e as Error).message }
    },
    null,
  )
  const _isLocked = FLOW_LOCKED.includes(item.status)

  return (
    <main className="container mx-auto p-4 max-w-xl">
      <div className="flex items-center gap-3 mb-6">
        <Link href="/interventions" className="text-muted-foreground hover:text-foreground">←</Link>
        <h1 className="text-2xl font-bold text-foreground">Modifier Intervention</h1>
      </div>

      {error && <p className="mb-4 text-sm text-red-600 bg-red-50 px-4 py-2 rounded">{error}</p>}
      {_isLocked && (
        <p className="mb-4 text-sm text-amber-800 bg-amber-50 border border-amber-200 px-4 py-2 rounded">
          Les informations ne sont plus modifiables à ce stade. Vous pouvez encore faire évoluer l&apos;état.
        </p>
      )}

      <form action={formAction} className="space-y-4 bg-card rounded-lg shadow-sm border border-border p-4">
        <div>
          <label htmlFor="date" className="block text-sm font-medium text-foreground mb-1">
            Date
          </label>
          <input
            type="datetime-local"
            id="date"
            name="date"
            defaultValue={item.date ? new Date(item.date as string).toISOString().slice(0, 16) : ''}
disabled={_isLocked}            className="w-full px-3 py-2 border border-border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary disabled:bg-muted disabled:text-muted-foreground"
          />
        </div>

        <div>
          <label htmlFor="clientId" className="block text-sm font-medium text-foreground mb-1">
            Client
          </label>
          <select
            id="clientId"
            name="clientId"
            defaultValue={item.clientId ?? ''}
disabled={_isLocked}            className="w-full px-3 py-2 border border-border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary disabled:bg-muted disabled:text-muted-foreground"
          >
            <option value="">Sélectionner…</option>
            {clientOptions.map(opt => (
              <option key={opt.id} value={opt.id}>{String(opt.name ?? opt.id)}</option>
            ))}
          </select>
        </div>
        <div>
          <label htmlFor="technicianId" className="block text-sm font-medium text-foreground mb-1">
            Technicien
          </label>
          <select
            id="technicianId"
            name="technicianId"
            defaultValue={item.technicianId ?? ''}
disabled={_isLocked}            className="w-full px-3 py-2 border border-border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary disabled:bg-muted disabled:text-muted-foreground"
          >
            <option value="">Sélectionner…</option>
            {technicianOptions.map(opt => (
              <option key={opt.id} value={opt.id}>{String(opt.name ?? opt.id)}</option>
            ))}
          </select>
        </div>


        <div className="flex gap-3 pt-2">
          <button
            type="submit"
            disabled={isPending}
            className="flex-1 px-6 py-2 bg-primary text-white rounded-md text-sm font-medium hover:bg-primary/85 disabled:opacity-50"
          >
            {isPending ? 'En cours…' : 'Enregistrer'}
          </button>
          <Link
            href="/interventions"
            className="px-6 py-2 border border-border rounded-md text-sm font-medium text-foreground hover:bg-muted/50"
          >
            Annuler
          </Link>
        </div>
      </form>
    </main>
  )
}
