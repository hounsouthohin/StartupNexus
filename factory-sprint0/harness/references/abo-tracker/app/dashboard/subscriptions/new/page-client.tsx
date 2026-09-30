'use client'

import { useActionState } from 'react'
import Link from 'next/link'
import { createSubscription } from '@/app/dashboard/subscriptions/actions'
import type { SerializedCategory } from '@/lib/types'

interface DashboardSubscriptionsNewClientProps {
  categoryOptions: SerializedCategory[]
}

export default function DashboardSubscriptionsNewClient({ categoryOptions }: DashboardSubscriptionsNewClientProps) {
  const [error, formAction, isPending] = useActionState(
    async (_prev: unknown, formData: FormData) => {
      try { await createSubscription(formData); return null }
      catch (e) { return (e as Error).message }
    },
    null,
  )

  return (
    <main className="container mx-auto p-6 max-w-xl">
      <div className="flex items-center gap-3 mb-6">
        <Link href="/dashboard/subscriptions" className="text-muted-foreground hover:text-foreground">←</Link>
        <h1 className="text-2xl font-bold text-foreground">Créer Abonnement</h1>
      </div>

      {error && <p className="mb-4 text-sm text-red-600 bg-red-50 px-4 py-2 rounded">{error}</p>}

      <form action={formAction} className="space-y-4 bg-card rounded-lg shadow-sm border border-border p-6">
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
          <label htmlFor="monthlyPrice" className="block text-sm font-medium text-foreground mb-1">
            Prix mensuel <span className="text-red-500">*</span>          </label>
          <input
            type="number"
            id="monthlyPrice"
            name="monthlyPrice"
required step="any"            className="w-full px-3 py-2 border border-border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary"
          />
        </div>
        <div>
          <label htmlFor="nextBillingDate" className="block text-sm font-medium text-foreground mb-1">
            Prochain prélèvement <span className="text-red-500">*</span>          </label>
          <input
            type="datetime-local"
            id="nextBillingDate"
            name="nextBillingDate"
required             className="w-full px-3 py-2 border border-border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary"
          />
        </div>

        <div>
          <label htmlFor="categoryId" className="block text-sm font-medium text-foreground mb-1">
            Catégorie
          </label>
          <select
            id="categoryId"
            name="categoryId"
            required
            className="w-full px-3 py-2 border border-border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary"
          >
            <option value="">Sélectionner…</option>
            {categoryOptions.map(opt => (
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
            href="/dashboard/subscriptions"
            className="px-6 py-2 border border-border rounded-md text-sm font-medium text-foreground hover:bg-muted/50"
          >
            Annuler
          </Link>
        </div>
      </form>
    </main>
  )
}
