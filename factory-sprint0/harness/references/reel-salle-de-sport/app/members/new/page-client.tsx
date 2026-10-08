'use client'

import { useActionState } from 'react'
import Link from 'next/link'
import { createMember } from '@/app/members/actions'
import type { SerializedSubscription } from '@/lib/types'

interface MembersNewClientProps {
  subscriptionOptions: SerializedSubscription[]
}

export default function MembersNewClient({ subscriptionOptions }: MembersNewClientProps) {
  const [error, formAction, isPending] = useActionState(
    async (_prev: unknown, formData: FormData) => {
      try { await createMember(formData); return null }
      catch (e) { return (e as Error).message }
    },
    null,
  )

  return (
    <main className="container mx-auto p-8 max-w-xl">
      <div className="flex items-center gap-3 mb-6">
        <Link href="/members" className="text-muted-foreground hover:text-foreground">←</Link>
        <h1 className="text-2xl font-bold text-foreground">Créer Membre</h1>
      </div>

      {error && <p className="mb-4 text-sm text-red-600 bg-red-50 px-4 py-2 rounded">{error}</p>}

      <form action={formAction} className="space-y-4 bg-card rounded-lg shadow-sm border border-border p-8">

        <div>
          <label htmlFor="subscriptionId" className="block text-sm font-medium text-foreground mb-1">
            Identifiant abonnement
          </label>
          <select
            id="subscriptionId"
            name="subscriptionId"
            required
            className="w-full px-3 py-2 border border-border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary"
          >
            <option value="">Sélectionner…</option>
            {subscriptionOptions.map(opt => (
              <option key={opt.id} value={opt.id}>{String(opt.status ?? opt.id)}</option>
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
            href="/members"
            className="px-6 py-2 border border-border rounded-md text-sm font-medium text-foreground hover:bg-muted/50"
          >
            Annuler
          </Link>
        </div>
      </form>
    </main>
  )
}
