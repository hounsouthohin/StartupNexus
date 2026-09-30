'use client'

import { useActionState } from 'react'
import Link from 'next/link'
import type { SerializedSubscription } from '@/lib/types'
import type { SerializedCategory } from '@/lib/types'
import { updateSubscription } from '@/app/dashboard/subscriptions/actions'


interface SubscriptionEditClientProps {
  item: SerializedSubscription
  categoryOptions: SerializedCategory[]
}

export default function SubscriptionEditClient({ item, categoryOptions }: SubscriptionEditClientProps) {
  const [error, formAction, isPending] = useActionState(
    async (_prev: unknown, formData: FormData) => {
      try { await updateSubscription.bind(null, item.id)(formData); return null }
      catch (e) { return (e as Error).message }
    },
    null,
  )

  return (
    <main className="container mx-auto p-6 max-w-xl">
      <div className="flex items-center gap-3 mb-6">
        <Link href="/dashboard/subscriptions" className="text-muted-foreground hover:text-foreground">←</Link>
        <h1 className="text-2xl font-bold text-foreground">Modifier Abonnement</h1>
      </div>

      {error && <p className="mb-4 text-sm text-red-600 bg-red-50 px-4 py-2 rounded">{error}</p>}

      <form action={formAction} className="space-y-4 bg-card rounded-lg shadow-sm border border-border p-6">
        <div>
          <label htmlFor="name" className="block text-sm font-medium text-foreground mb-1">
            Nom
          </label>
          <input
            type="text"
            id="name"
            name="name"
            defaultValue={item.name != null ? String(item.name) : ''}
            className="w-full px-3 py-2 border border-border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary disabled:bg-muted disabled:text-muted-foreground"
          />
        </div>
        <div>
          <label htmlFor="monthlyPrice" className="block text-sm font-medium text-foreground mb-1">
            Prix mensuel
          </label>
          <input
            type="number"
            id="monthlyPrice"
            name="monthlyPrice"
            defaultValue={item.monthlyPrice != null ? String(item.monthlyPrice) : ''}
step="any"             className="w-full px-3 py-2 border border-border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary disabled:bg-muted disabled:text-muted-foreground"
          />
        </div>
        <div>
          <label htmlFor="nextBillingDate" className="block text-sm font-medium text-foreground mb-1">
            Prochain prélèvement
          </label>
          <input
            type="datetime-local"
            id="nextBillingDate"
            name="nextBillingDate"
            defaultValue={item.nextBillingDate ? new Date(item.nextBillingDate as string).toISOString().slice(0, 16) : ''}
            className="w-full px-3 py-2 border border-border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary disabled:bg-muted disabled:text-muted-foreground"
          />
        </div>

        <div>
          <label htmlFor="categoryId" className="block text-sm font-medium text-foreground mb-1">
            Catégorie
          </label>
          <select
            id="categoryId"
            name="categoryId"
            defaultValue={item.categoryId ?? ''}
            className="w-full px-3 py-2 border border-border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary disabled:bg-muted disabled:text-muted-foreground"
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
            {isPending ? 'En cours…' : 'Enregistrer'}
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
