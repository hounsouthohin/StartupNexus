'use client'

import { useActionState } from 'react'
import Link from 'next/link'
import { createProvider } from '@/app/dashboard/providers/actions'
import type { SerializedManager } from '@/lib/types'

interface DashboardProvidersNewClientProps {
  managerOptions: SerializedManager[]
}

export default function DashboardProvidersNewClient({ managerOptions }: DashboardProvidersNewClientProps) {
  const [error, formAction, isPending] = useActionState(
    async (_prev: unknown, formData: FormData) => {
      try { await createProvider(formData); return null }
      catch (e) { return (e as Error).message }
    },
    null,
  )

  return (
    <main className="container mx-auto p-4 max-w-xl">
      <div className="flex items-center gap-3 mb-6">
        <Link href="/dashboard/providers" className="text-muted-foreground hover:text-foreground">←</Link>
        <h1 className="text-2xl font-bold text-foreground">Créer Prestataire</h1>
      </div>

      {error && <p className="mb-4 text-sm text-red-600 bg-red-50 px-4 py-2 rounded">{error}</p>}

      <form action={formAction} className="space-y-4 bg-card rounded-lg shadow-sm border border-border p-4">
        <div>
          <label htmlFor="name" className="block text-sm font-medium text-foreground mb-1">
            Nom <span className="text-red-500">*</span>          </label>
          <input
            type="text"
            id="name"
            name="name"
required             className="w-full px-3 py-2 border border-border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary"
          />
        </div>
        <div>
          <label htmlFor="email" className="block text-sm font-medium text-foreground mb-1">
            Email <span className="text-red-500">*</span>          </label>
          <input
            type="email"
            id="email"
            name="email"
required             className="w-full px-3 py-2 border border-border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary"
          />
        </div>


        <div>
          <span className="block text-sm font-medium text-foreground mb-1">Gestionnaires</span>
          <div className="max-h-40 overflow-y-auto border border-border rounded-md p-3 space-y-2">
            {managerOptions.length === 0 ? (
              <p className="text-sm text-muted-foreground">Aucun élément disponible.</p>
            ) : managerOptions.map(opt => (
              <label key={opt.id} className="flex items-center gap-2 text-sm text-foreground">
                <input
                  type="checkbox"
                  name="managerIds"
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
            href="/dashboard/providers"
            className="px-6 py-2 border border-border rounded-md text-sm font-medium text-foreground hover:bg-muted/50"
          >
            Annuler
          </Link>
        </div>
      </form>
    </main>
  )
}
