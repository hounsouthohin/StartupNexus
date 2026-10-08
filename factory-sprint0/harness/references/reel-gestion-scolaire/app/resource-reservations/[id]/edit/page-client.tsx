'use client'

import { useActionState } from 'react'
import Link from 'next/link'
import type { SerializedResourceReservation } from '@/lib/types'
import type { SerializedDigitalResource } from '@/lib/types'
import { updateResourceReservation } from '@/app/resource-reservations/actions'


interface ResourceReservationEditClientProps {
  item: SerializedResourceReservation
  digitalResourceOptions: SerializedDigitalResource[]
}

export default function ResourceReservationEditClient({ item, digitalResourceOptions }: ResourceReservationEditClientProps) {
  const [error, formAction, isPending] = useActionState(
    async (_prev: unknown, formData: FormData) => {
      try { await updateResourceReservation.bind(null, item.id)(formData); return null }
      catch (e) { return (e as Error).message }
    },
    null,
  )

  return (
    <main className="container mx-auto p-6 max-w-xl">
      <div className="flex items-center gap-3 mb-6">
        <Link href="/resource-reservations" className="text-muted-foreground hover:text-foreground">←</Link>
        <h1 className="text-2xl font-bold text-foreground">Modifier Réservation de ressource</h1>
      </div>

      {error && <p className="mb-4 text-sm text-red-600 bg-red-50 px-4 py-2 rounded">{error}</p>}

      <form action={formAction} className="space-y-4 bg-card rounded-lg shadow-sm border border-border p-6">
        <div>
          <label htmlFor="date" className="block text-sm font-medium text-foreground mb-1">
            Date
          </label>
          <input
            type="datetime-local"
            id="date"
            name="date"
            defaultValue={item.date ? new Date(item.date as string).toISOString().slice(0, 16) : ''}
            className="w-full px-3 py-2 border border-border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary disabled:bg-muted disabled:text-muted-foreground"
          />
        </div>

        <div>
          <label htmlFor="resourceId" className="block text-sm font-medium text-foreground mb-1">
            ID Ressource
          </label>
          <select
            id="resourceId"
            name="resourceId"
            defaultValue={item.resourceId ?? ''}
            className="w-full px-3 py-2 border border-border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary disabled:bg-muted disabled:text-muted-foreground"
          >
            <option value="">Sélectionner…</option>
            {digitalResourceOptions.map(opt => (
              <option key={opt.id} value={opt.id}>{String(opt.title ?? opt.id)}</option>
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
            href="/resource-reservations"
            className="px-6 py-2 border border-border rounded-md text-sm font-medium text-foreground hover:bg-muted/50"
          >
            Annuler
          </Link>
        </div>
      </form>
    </main>
  )
}
