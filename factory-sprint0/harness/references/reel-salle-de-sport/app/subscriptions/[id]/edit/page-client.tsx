'use client'

import { useActionState } from 'react'
import Link from 'next/link'
import type { SerializedSubscription } from '@/lib/types'
import { updateSubscription } from '@/app/subscriptions/actions'

// Verrou d'édition (type I) : dans ces états les champs métier sont figés. Le changement
// d'état lui-même se fait via les boutons de transition de la page détail, pas ici.
const FLOW_LOCKED: string[] = ["cancelled"]

interface SubscriptionEditClientProps {
  item: SerializedSubscription
}

export default function SubscriptionEditClient({ item }: SubscriptionEditClientProps) {
  const [error, formAction, isPending] = useActionState(
    async (_prev: unknown, formData: FormData) => {
      try { await updateSubscription.bind(null, item.id)(formData); return null }
      catch (e) { return (e as Error).message }
    },
    null,
  )
  const _isLocked = FLOW_LOCKED.includes(item.status)

  return (
    <main className="container mx-auto p-8 max-w-xl">
      <div className="flex items-center gap-3 mb-6">
        <Link href="/subscriptions" className="text-muted-foreground hover:text-foreground">←</Link>
        <h1 className="text-2xl font-bold text-foreground">Modifier Abonnement</h1>
      </div>

      {error && <p className="mb-4 text-sm text-red-600 bg-red-50 px-4 py-2 rounded">{error}</p>}
      {_isLocked && (
        <p className="mb-4 text-sm text-amber-800 bg-amber-50 border border-amber-200 px-4 py-2 rounded">
          Les informations ne sont plus modifiables à ce stade. Vous pouvez encore faire évoluer l&apos;état.
        </p>
      )}

      <form action={formAction} className="space-y-4 bg-card rounded-lg shadow-sm border border-border p-8">
        <div>
          <label htmlFor="renewalDate" className="block text-sm font-medium text-foreground mb-1">
            Date de renouvellement
          </label>
          <input
            type="date"
            id="renewalDate"
            name="renewalDate"
            defaultValue={item.renewalDate ? (item.renewalDate as string).slice(0, 10) : ''}
disabled={_isLocked}            className="w-full px-3 py-2 border border-border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary disabled:bg-muted disabled:text-muted-foreground"
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
            href="/subscriptions"
            className="px-6 py-2 border border-border rounded-md text-sm font-medium text-foreground hover:bg-muted/50"
          >
            Annuler
          </Link>
        </div>
      </form>
    </main>
  )
}
