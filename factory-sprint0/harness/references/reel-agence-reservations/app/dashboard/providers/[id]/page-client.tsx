'use client'

import { useState, useActionState } from 'react'
import Link from 'next/link'
import type { SerializedProvider } from '@/lib/types'
import type { SerializedReservation } from '@/lib/types'
import { createReservation, deleteReservation } from '@/app/dashboard/reservations/actions'
import type { SerializedClient } from '@/lib/types'
import { createClient, deleteClient } from '@/app/dashboard/clients/actions'

interface DashboardProvidersIdClientProps {
  item: SerializedProvider
}

export default function DashboardProvidersIdClient({ item }: DashboardProvidersIdClientProps) {
  const [reservationList, setReservationList] = useState<SerializedReservation[]>(
    (item.reservations as SerializedReservation[] | undefined) ?? []
  )
  const [clientList, setClientList] = useState<SerializedClient[]>(
    (item.clients as SerializedClient[] | undefined) ?? []
  )

  const [reservationError, reservationFormAction, reservationPending] = useActionState(
    async (_prev: unknown, formData: FormData) => {
      formData.set('providerId', item.id)
      try {
        await createReservation(formData)
        return null
      } catch (e) {
        return (e as Error).message
      }
    },
    null,
  )

  const handleDeleteReservation = async (id: string) => {
    if (!confirm('Supprimer cet élément ?')) return
    await deleteReservation(id)
    setReservationList(prev => prev.filter(c => c.id !== id))
  }

  const [clientError, clientFormAction, clientPending] = useActionState(
    async (_prev: unknown, formData: FormData) => {
      formData.set('providerId', item.id)
      try {
        await createClient(formData)
        return null
      } catch (e) {
        return (e as Error).message
      }
    },
    null,
  )

  const handleDeleteClient = async (id: string) => {
    if (!confirm('Supprimer cet élément ?')) return
    await deleteClient(id)
    setClientList(prev => prev.filter(c => c.id !== id))
  }

  return (
    <main className="container mx-auto p-4 max-w-4xl">
      {/* ── Détail Provider ── */}
      <div className="mb-8">
        <div className="flex items-center gap-4 mb-6">
          <Link href="/dashboard/providers" className="text-muted-foreground hover:text-foreground text-sm">
            ← Prestataires
          </Link>
        </div>
        <div className="bg-card rounded-lg shadow-sm border border-border p-4 space-y-3">
          <div>
            <span className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Nom</span>
            <p className="mt-1 text-sm text-foreground">
              {String(item.name ?? '')}
            </p>
          </div>
          <div>
            <span className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Email</span>
            <p className="mt-1 text-sm text-foreground">
              {String(item.email ?? '')}
            </p>
          </div>
        </div>
      </div>

      {/* ── Réservations ── */}
      <section className="mb-8">
        <h2 className="text-lg font-semibold text-foreground mb-4">Réservations</h2>

        {/* Liste */}
        {reservationList.length === 0 ? (
          <p className="text-muted-foreground text-sm py-4 text-center">Aucun élément pour l'instant.</p>
        ) : (
          <ul className="space-y-3 mb-6">
            {reservationList.map(c => (
              <li key={c.id} className="bg-card rounded-lg border border-border p-4 flex items-start justify-between gap-4">
                <div className="flex-1 space-y-1">
                  <p className="text-sm text-foreground">{String(c.date ?? '')}</p>
                  <p className="text-sm text-foreground">{String(c.status ?? '')}</p>
                </div>
                <div className="flex shrink-0 gap-2 items-center">
                  <Link href={`/dashboard/reservations/${c.id}`} className="text-xs text-primary border border-primary rounded px-2 py-1 hover:bg-primary/10">
                    Voir
                  </Link>
                  <button
                    type="button"
                    onClick={() => handleDeleteReservation(c.id)}
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
        {reservationError && (
          <p className="mb-3 text-sm text-red-600 bg-red-50 px-4 py-2 rounded">{reservationError}</p>
        )}
        <form action={reservationFormAction} className="bg-muted rounded-lg border border-border p-4 space-y-3">
          <div>
            <label htmlFor="reservation_date" className="block text-xs font-medium text-foreground mb-1">
              Date <span className="text-red-500">*</span>            </label>
            <input
              type="datetime-local"
              id="reservation_date"
              name="date"
required              className="w-full px-3 py-2 border border-border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>
          <div>
            <label htmlFor="reservation_status" className="block text-xs font-medium text-foreground mb-1">
              Statut            </label>
            <select
              id="reservation_status"
              name="status"
              className="w-full px-3 py-2 border border-border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            >
              <option value="">Sélectionner…</option>
              <option value="pending">En attente</option>
              <option value="confirmed">Confirmée</option>
              <option value="cancelled">Annulée</option>
            </select>
          </div>
          <button
            type="submit"
            disabled={reservationPending}
            className="px-4 py-2 bg-primary text-white rounded-md text-sm font-medium hover:bg-primary/85 disabled:opacity-50"
          >
            {reservationPending ? 'En cours…' : 'Ajouter'}
          </button>
        </form>
      </section>
      {/* ── Clients ── */}
      <section className="mb-8">
        <h2 className="text-lg font-semibold text-foreground mb-4">Clients</h2>

        {/* Liste */}
        {clientList.length === 0 ? (
          <p className="text-muted-foreground text-sm py-4 text-center">Aucun élément pour l'instant.</p>
        ) : (
          <ul className="space-y-3 mb-6">
            {clientList.map(c => (
              <li key={c.id} className="bg-card rounded-lg border border-border p-4 flex items-start justify-between gap-4">
                <div className="flex-1 space-y-1">
                  <p className="text-sm text-foreground">{String(c.name ?? '')}</p>
                  <p className="text-sm text-foreground">{String(c.email ?? '')}</p>
                </div>
                <div className="flex shrink-0 gap-2 items-center">
                  <Link href={`/dashboard/clients/${c.id}`} className="text-xs text-primary border border-primary rounded px-2 py-1 hover:bg-primary/10">
                    Voir
                  </Link>
                  <button
                    type="button"
                    onClick={() => handleDeleteClient(c.id)}
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
        {clientError && (
          <p className="mb-3 text-sm text-red-600 bg-red-50 px-4 py-2 rounded">{clientError}</p>
        )}
        <form action={clientFormAction} className="bg-muted rounded-lg border border-border p-4 space-y-3">
          <div>
            <label htmlFor="client_name" className="block text-xs font-medium text-foreground mb-1">
              Nom <span className="text-red-500">*</span>            </label>
            <input
              type="text"
              id="client_name"
              name="name"
required              className="w-full px-3 py-2 border border-border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>
          <div>
            <label htmlFor="client_email" className="block text-xs font-medium text-foreground mb-1">
              Email <span className="text-red-500">*</span>            </label>
            <input
              type="email"
              id="client_email"
              name="email"
required              className="w-full px-3 py-2 border border-border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>
          <button
            type="submit"
            disabled={clientPending}
            className="px-4 py-2 bg-primary text-white rounded-md text-sm font-medium hover:bg-primary/85 disabled:opacity-50"
          >
            {clientPending ? 'En cours…' : 'Ajouter'}
          </button>
        </form>
      </section>
    </main>
  )
}
