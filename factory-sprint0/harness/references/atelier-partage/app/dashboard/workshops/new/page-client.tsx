'use client'

import { useActionState } from 'react'
import Link from 'next/link'
import { createWorkshop } from '@/app/dashboard/workshops/actions'
import type { SerializedDomain } from '@/lib/types'

interface DashboardWorkshopsNewClientProps {
  domainOptions: SerializedDomain[]
}

export default function DashboardWorkshopsNewClient({ domainOptions }: DashboardWorkshopsNewClientProps) {
  const [error, formAction, isPending] = useActionState(
    async (_prev: unknown, formData: FormData) => {
      try { await createWorkshop(formData); return null }
      catch (e) { return (e as Error).message }
    },
    null,
  )

  return (
    <main className="container mx-auto p-6 max-w-xl">
      <div className="flex items-center gap-3 mb-6">
        <Link href="/dashboard/workshops" className="text-muted-foreground hover:text-foreground">←</Link>
        <h1 className="text-2xl font-bold text-foreground">Créer Atelier</h1>
      </div>

      {error && <p className="mb-4 text-sm text-red-600 bg-red-50 px-4 py-2 rounded">{error}</p>}

      <form action={formAction} className="space-y-4 bg-card rounded-lg border-2 border-border p-6">
        <div>
          <label htmlFor="title" className="block text-sm font-medium text-foreground mb-1">
            Titre <span className="text-red-500">*</span>          </label>
          <input
            type="text"
            id="title"
            name="title"
required             className="w-full px-3 py-2 border border-border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary"
          />
        </div>
        <div>
          <label htmlFor="description" className="block text-sm font-medium text-foreground mb-1">
            Description <span className="text-red-500">*</span>          </label>
          <textarea
            id="description"
            name="description"
            rows={4}
required            className="w-full px-3 py-2 border border-border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary"
          />
        </div>
        <div>
          <label htmlFor="duration" className="block text-sm font-medium text-foreground mb-1">
            Durée <span className="text-red-500">*</span>          </label>
          <input
            type="number"
            id="duration"
            name="duration"
required step="any"            className="w-full px-3 py-2 border border-border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary"
          />
        </div>
        <div>
          <label htmlFor="price" className="block text-sm font-medium text-foreground mb-1">
            Prix <span className="text-red-500">*</span>          </label>
          <input
            type="number"
            id="price"
            name="price"
required step="any"            className="w-full px-3 py-2 border border-border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary"
          />
        </div>


        <div>
          <span className="block text-sm font-medium text-foreground mb-1">Domaines</span>
          <div className="max-h-40 overflow-y-auto border border-border rounded-md p-3 space-y-2">
            {domainOptions.length === 0 ? (
              <p className="text-sm text-muted-foreground">Aucun élément disponible.</p>
            ) : domainOptions.map(opt => (
              <label key={opt.id} className="flex items-center gap-2 text-sm text-foreground">
                <input
                  type="checkbox"
                  name="domainIds"
                  value={opt.id}
                  className="h-4 w-4 text-primary border-border rounded"
                />
                <span>{String(opt.name ?? opt.id)}</span>
              </label>
            ))}
          </div>
        </div>

        <div className="flex gap-3 pt-2">
          <button
            type="submit"
            disabled={isPending}
            className="flex-1 px-6 py-2 bg-primary text-white rounded-md text-sm font-medium hover:bg-primary/85 disabled:opacity-50"
          >
            {isPending ? 'En cours…' : 'Créer'}
          </button>
          <Link
            href="/dashboard/workshops"
            className="px-6 py-2 border border-border rounded-md text-sm font-medium text-foreground hover:bg-muted/50"
          >
            Annuler
          </Link>
        </div>
      </form>
    </main>
  )
}
