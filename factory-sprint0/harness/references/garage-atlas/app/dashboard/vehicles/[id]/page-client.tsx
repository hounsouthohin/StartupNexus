'use client'

import { useState, useActionState } from 'react'
import Link from 'next/link'
import type { SerializedVehicle } from '@/lib/types'
import type { SerializedRepair } from '@/lib/types'
import { createRepair, deleteRepair } from '@/app/dashboard/repairs/actions'

interface DashboardVehiclesIdClientProps {
  item: SerializedVehicle
}

export default function DashboardVehiclesIdClient({ item }: DashboardVehiclesIdClientProps) {
  const [repairList, setRepairList] = useState<SerializedRepair[]>(
    (item.repairs as SerializedRepair[] | undefined) ?? []
  )

  const [repairError, repairFormAction, repairPending] = useActionState(
    async (_prev: unknown, formData: FormData) => {
      formData.set('vehicleId', item.id)
      try {
        await createRepair(formData)
        return null
      } catch (e) {
        return (e as Error).message
      }
    },
    null,
  )

  const handleDeleteRepair = async (id: string) => {
    if (!confirm('Supprimer cet élément ?')) return
    await deleteRepair(id)
    setRepairList(prev => prev.filter(c => c.id !== id))
  }

  return (
    <main className="container mx-auto p-4 max-w-4xl">
      {/* ── Détail Vehicle ── */}
      <div className="mb-8">
        <div className="flex items-center gap-4 mb-6">
          <Link href="/dashboard/vehicles" className="text-muted-foreground hover:text-foreground text-sm">
            ← Véhicules
          </Link>
        </div>
        <div className="bg-card rounded-lg shadow-sm border border-border p-4 space-y-3">
          <div>
            <span className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Marque</span>
            <p className="mt-1 text-sm text-foreground">
              {String(item.brand ?? '')}
            </p>
          </div>
          <div>
            <span className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Modèle</span>
            <p className="mt-1 text-sm text-foreground">
              {String(item.model ?? '')}
            </p>
          </div>
          <div>
            <span className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Plaque d'immatriculation</span>
            <p className="mt-1 text-sm text-foreground">
              {String(item.licensePlate ?? '')}
            </p>
          </div>
        </div>
      </div>

      {/* ── Réparations ── */}
      <section className="mb-8">
        <h2 className="text-lg font-semibold text-foreground mb-4">Réparations</h2>

        {/* Liste */}
        {repairList.length === 0 ? (
          <p className="text-muted-foreground text-sm py-4 text-center">Aucun élément pour l'instant.</p>
        ) : (
          <ul className="space-y-3 mb-6">
            {repairList.map(c => (
              <li key={c.id} className="bg-card rounded-lg border border-border p-4 flex items-start justify-between gap-4">
                <div className="flex-1 space-y-1">
                  <p className="text-sm text-foreground">{String(c.description ?? '')}</p>
                  <p className="text-sm text-foreground">{String(c.status ?? '')}</p>
                  <p className="text-sm text-foreground">{String(c.reasonForRejection ?? '')}</p>
                </div>
                <div className="flex shrink-0 gap-2 items-center">
                  <Link href={`/dashboard/repairs/${c.id}`} className="text-xs text-primary border border-primary rounded px-2 py-1 hover:bg-primary/10">
                    Voir
                  </Link>
                  <button
                    type="button"
                    onClick={() => handleDeleteRepair(c.id)}
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
        {repairError && (
          <p className="mb-3 text-sm text-red-600 bg-red-50 px-4 py-2 rounded">{repairError}</p>
        )}
        <form action={repairFormAction} className="bg-muted rounded-lg border border-border p-4 space-y-3">
          <div>
            <label htmlFor="repair_description" className="block text-xs font-medium text-foreground mb-1">
              Description <span className="text-red-500">*</span>            </label>
            <textarea
              id="repair_description"
              name="description"
              rows={3}
required              className="w-full px-3 py-2 border border-border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>
          <div>
            <label htmlFor="repair_status" className="block text-xs font-medium text-foreground mb-1">
              Statut            </label>
            <select
              id="repair_status"
              name="status"
              className="w-full px-3 py-2 border border-border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            >
              <option value="">Sélectionner…</option>
              <option value="pending">En attente</option>
              <option value="accepted">Acceptée</option>
              <option value="rejected">Rejetée</option>
              <option value="in_progress">En cours</option>
              <option value="completed">Terminée</option>
            </select>
          </div>
          <div>
            <label htmlFor="repair_reasonForRejection" className="block text-xs font-medium text-foreground mb-1">
              Raison du refus            </label>
            <input
              type="text"
              id="repair_reasonForRejection"
              name="reasonForRejection"
              className="w-full px-3 py-2 border border-border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>
          <div>
            <label htmlFor="repair_amountCharged" className="block text-xs font-medium text-foreground mb-1">
              Montant facturé            </label>
            <input
              type="number"
              id="repair_amountCharged"
              name="amountCharged"
              className="w-full px-3 py-2 border border-border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>
          <button
            type="submit"
            disabled={repairPending}
            className="px-4 py-2 bg-primary text-white rounded-md text-sm font-medium hover:bg-primary/85 disabled:opacity-50"
          >
            {repairPending ? 'En cours…' : 'Ajouter'}
          </button>
        </form>
      </section>
    </main>
  )
}
