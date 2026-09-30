'use client'

import { useActionState } from 'react'
import Link from 'next/link'
import type { SerializedRunEvent } from '@/lib/types'
import { updateRunEvent } from '@/app/dashboard/run-events/actions'


interface RunEventEditClientProps {
  item: SerializedRunEvent
}

export default function RunEventEditClient({ item }: RunEventEditClientProps) {
  const [error, formAction, isPending] = useActionState(
    async (_prev: unknown, formData: FormData) => {
      try { await updateRunEvent.bind(null, item.id)(formData); return null }
      catch (e) { return (e as Error).message }
    },
    null,
  )

  return (
    <main className="container mx-auto p-6 max-w-xl">
      <div className="flex items-center gap-3 mb-6">
        <Link href="/dashboard/run-events" className="text-muted-foreground hover:text-foreground">←</Link>
        <h1 className="text-2xl font-bold text-foreground">Modifier Sortie</h1>
      </div>

      {error && <p className="mb-4 text-sm text-red-600 bg-red-50 px-4 py-2 rounded">{error}</p>}

      <form action={formAction} className="space-y-4 bg-card rounded-lg shadow-sm border border-border p-6">
        <div>
          <label htmlFor="title" className="block text-sm font-medium text-foreground mb-1">
            Titre
          </label>
          <input
            type="text"
            id="title"
            name="title"
            defaultValue={item.title != null ? String(item.title) : ''}
            className="w-full px-3 py-2 border border-border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary disabled:bg-muted disabled:text-muted-foreground"
          />
        </div>
        <div>
          <label htmlFor="dateTime" className="block text-sm font-medium text-foreground mb-1">
            Date et Heure
          </label>
          <input
            type="datetime-local"
            id="dateTime"
            name="dateTime"
            defaultValue={item.dateTime ? new Date(item.dateTime as string).toISOString().slice(0, 16) : ''}
            className="w-full px-3 py-2 border border-border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary disabled:bg-muted disabled:text-muted-foreground"
          />
        </div>
        <div>
          <label htmlFor="location" className="block text-sm font-medium text-foreground mb-1">
            Lieu de départ
          </label>
          <input
            type="text"
            id="location"
            name="location"
            defaultValue={item.location != null ? String(item.location) : ''}
            className="w-full px-3 py-2 border border-border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary disabled:bg-muted disabled:text-muted-foreground"
          />
        </div>
        <div>
          <label htmlFor="distance" className="block text-sm font-medium text-foreground mb-1">
            Distance (km)
          </label>
          <input
            type="number"
            id="distance"
            name="distance"
            defaultValue={item.distance != null ? String(item.distance) : ''}
step="any"             className="w-full px-3 py-2 border border-border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary disabled:bg-muted disabled:text-muted-foreground"
          />
        </div>
        <div>
          <label htmlFor="description" className="block text-sm font-medium text-foreground mb-1">
            Description du parcours
          </label>
          <textarea
            id="description"
            name="description"
            rows={4}
            defaultValue={item.description ?? ''}
            className="w-full px-3 py-2 border border-border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary disabled:bg-muted disabled:text-muted-foreground"
          />
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
            href="/dashboard/run-events"
            className="px-6 py-2 border border-border rounded-md text-sm font-medium text-foreground hover:bg-muted/50"
          >
            Annuler
          </Link>
        </div>
      </form>
    </main>
  )
}
