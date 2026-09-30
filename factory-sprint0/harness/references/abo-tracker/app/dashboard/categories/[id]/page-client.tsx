'use client'

import { useState, useActionState } from 'react'
import Link from 'next/link'
import type { SerializedCategory } from '@/lib/types'
import type { SerializedSubscription } from '@/lib/types'
import { createSubscription, deleteSubscription } from '@/app/dashboard/subscriptions/actions'

interface DashboardCategoriesIdClientProps {
  item: SerializedCategory
}

export default function DashboardCategoriesIdClient({ item }: DashboardCategoriesIdClientProps) {
  const [subscriptionList, setSubscriptionList] = useState<SerializedSubscription[]>(
    (item.subscriptions as SerializedSubscription[] | undefined) ?? []
  )

  const [subscriptionError, subscriptionFormAction, subscriptionPending] = useActionState(
    async (_prev: unknown, formData: FormData) => {
      formData.set('categoryId', item.id)
      try {
        await createSubscription(formData)
        return null
      } catch (e) {
        return (e as Error).message
      }
    },
    null,
  )

  const handleDeleteSubscription = async (id: string) => {
    if (!confirm('Supprimer cet élément ?')) return
    await deleteSubscription(id)
    setSubscriptionList(prev => prev.filter(c => c.id !== id))
  }

  return (
    <main className="container mx-auto p-6 max-w-4xl">
      {/* ── Détail Category ── */}
      <div className="mb-8">
        <div className="flex items-center gap-4 mb-6">
          <Link href="/dashboard/categories" className="text-muted-foreground hover:text-foreground text-sm">
            ← Catégories
          </Link>
        </div>
        <div className="bg-card rounded-lg shadow-sm border border-border p-6 space-y-3">
          <div>
            <span className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Nom</span>
            <p className="mt-1 text-sm text-foreground">
              {String(item.name ?? '')}
            </p>
          </div>
          <div>
            <span className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Description</span>
            <p className="mt-1 text-sm text-foreground">
              {String(item.description ?? '')}
            </p>
          </div>
        </div>
      </div>

      {/* ── Abonnements ── */}
      <section className="mb-8">
        <h2 className="text-lg font-semibold text-foreground mb-4">Abonnements</h2>

        {/* Liste */}
        {subscriptionList.length === 0 ? (
          <p className="text-muted-foreground text-sm py-4 text-center">Aucun élément pour l'instant.</p>
        ) : (
          <ul className="space-y-3 mb-6">
            {subscriptionList.map(c => (
              <li key={c.id} className="bg-card rounded-lg border border-border p-4 flex items-start justify-between gap-4">
                <div className="flex-1 space-y-1">
                  <p className="text-sm text-foreground">{String(c.name ?? '')}</p>
                  <p className="text-sm text-foreground">{String(c.nextBillingDate ?? '')}</p>
                  <p className="text-sm text-foreground">{String(c.status ?? '')}</p>
                </div>
                <div className="flex shrink-0 gap-2 items-center">
                  <Link href={`/dashboard/subscriptions/${c.id}`} className="text-xs text-primary border border-primary rounded px-2 py-1 hover:bg-primary/10">
                    Voir
                  </Link>
                  <button
                    type="button"
                    onClick={() => handleDeleteSubscription(c.id)}
                    className="text-xs text-red-600 border border-red-200 rounded px-2 py-1 hover:bg-red-50"
                  >
                    Supprimer
                  </button>
                </div>
              </li>
            ))}
          </ul>
        )}

        {/* Formulaire de création */}
        {subscriptionError && (
          <p className="mb-3 text-sm text-red-600 bg-red-50 px-4 py-2 rounded">{subscriptionError}</p>
        )}
        <form action={subscriptionFormAction} className="bg-muted rounded-lg border border-border p-4 space-y-3">
          <div>
            <label htmlFor="subscription_name" className="block text-xs font-medium text-foreground mb-1">
              Nom <span className="text-red-500">*</span>            </label>
            <input
              type="text"
              id="subscription_name"
              name="name"
required              className="w-full px-3 py-2 border border-border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>
          <div>
            <label htmlFor="subscription_monthlyPrice" className="block text-xs font-medium text-foreground mb-1">
              Prix mensuel <span className="text-red-500">*</span>            </label>
            <input
              type="number"
              id="subscription_monthlyPrice"
              name="monthlyPrice"
required              className="w-full px-3 py-2 border border-border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>
          <div>
            <label htmlFor="subscription_nextBillingDate" className="block text-xs font-medium text-foreground mb-1">
              Prochain prélèvement <span className="text-red-500">*</span>            </label>
            <input
              type="datetime-local"
              id="subscription_nextBillingDate"
              name="nextBillingDate"
required              className="w-full px-3 py-2 border border-border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>
          <div>
            <label htmlFor="subscription_status" className="block text-xs font-medium text-foreground mb-1">
              Statut            </label>
            <select
              id="subscription_status"
              name="status"
              className="w-full px-3 py-2 border border-border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            >
              <option value="">Sélectionner…</option>
              <option value="active">Actif</option>
              <option value="paused">En pause</option>
              <option value="cancelled">Résilié</option>
            </select>
          </div>
          <button
            type="submit"
            disabled={subscriptionPending}
            className="px-4 py-2 bg-primary text-white rounded-md text-sm font-medium hover:bg-primary/85 disabled:opacity-50"
          >
            {subscriptionPending ? 'En cours…' : 'Ajouter'}
          </button>
        </form>
      </section>
    </main>
  )
}
