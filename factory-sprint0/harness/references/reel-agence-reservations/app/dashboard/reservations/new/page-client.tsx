'use client'

import { useActionState } from 'react'
import Link from 'next/link'
import { createReservation } from '@/app/dashboard/reservations/actions'
import type { SerializedProvider } from '@/lib/types'
import type { SerializedManager } from '@/lib/types'

interface DashboardReservationsNewClientProps {
  providerOptions: SerializedProvider[], managerOptions: SerializedManager[]
}

export default function DashboardReservationsNewClient({ providerOptions, managerOptions }: DashboardReservationsNewClientProps) {
  const [error, formAction, isPending] = useActionState(
    async (_prev: unknown, formData: FormData) => {
      try { await createReservation(formData); return null }
      catch (e) { return (e as Error).message }
    },
    null,
  )

  return (
    <main className="container mx-auto p-4 max-w-xl">
      <div className="flex items-center gap-3 mb-6">
        <Link href="/dashboard/reservations" className="text-muted-foreground hover:text-foreground">←</Link>
        <h1 className="text-2xl font-bold text-foreground">Créer Réservation</h1>
      </div>

      {error && <p className="mb-4 text-sm text-red-600 bg-red-50 px-4 py-2 rounded">{error}</p>}

      <form action={formAction} className="space-y-4 bg-card rounded-lg shadow-sm border border-border p-4">
        <div>
          <label htmlFor="date" className="block text-sm font-medium text-foreground mb-1">
            Date <span className="text-red-500">*</span>          </label>
          <input
            type="datetime-local"
            id="date"
            name="date"
required             className="w-full px-3 py-2 border border-border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary"
          />
        </div>

        <div>
          <label htmlFor="providerId" className="block text-sm font-medium text-foreground mb-1">
            Prestataire
          </label>
          <select
            id="providerId"
            name="providerId"
            required
            className="w-full px-3 py-2 border border-border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary"
          >
            <option value="">Sélectionner…</option>
            {providerOptions.map(opt => (
              <option key={opt.id} value={opt.id}>{String(opt.name ?? opt.id)}</option>
            ))}
          </select>
        </div>
        <div>
          <label htmlFor="managerId" className="block text-sm font-medium text-foreground mb-1">
            Gestionnaire
          </label>
          <select
            id="managerId"
            name="managerId"
            required
            className="w-full px-3 py-2 border border-border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary"
          >
            <option value="">Sélectionner…</option>
            {managerOptions.map(opt => (
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
            {isPending ? 'En cours…' : 'Créer'}
          </button>
          <Link
            href="/dashboard/reservations"
            className="px-6 py-2 border border-border rounded-md text-sm font-medium text-foreground hover:bg-muted/50"
          >
            Annuler
          </Link>
        </div>
      </form>
    </main>
  )
}
