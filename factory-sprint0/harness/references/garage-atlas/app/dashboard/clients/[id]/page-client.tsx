'use client'

import { useState, useActionState } from 'react'
import Link from 'next/link'
import type { SerializedClient } from '@/lib/types'
import type { SerializedVehicle } from '@/lib/types'
import { createVehicle, deleteVehicle } from '@/app/dashboard/vehicles/actions'

interface DashboardClientsIdClientProps {
  item: SerializedClient
}

export default function DashboardClientsIdClient({ item }: DashboardClientsIdClientProps) {
  const [vehicleList, setVehicleList] = useState<SerializedVehicle[]>(
    (item.vehicles as SerializedVehicle[] | undefined) ?? []
  )

  const [vehicleError, vehicleFormAction, vehiclePending] = useActionState(
    async (_prev: unknown, formData: FormData) => {
      formData.set('clientId', item.id)
      try {
        await createVehicle(formData)
        return null
      } catch (e) {
        return (e as Error).message
      }
    },
    null,
  )

  const handleDeleteVehicle = async (id: string) => {
    if (!confirm('Supprimer cet élément ?')) return
    await deleteVehicle(id)
    setVehicleList(prev => prev.filter(c => c.id !== id))
  }

  return (
    <main className="container mx-auto p-4 max-w-4xl">
      {/* ── Détail Client ── */}
      <div className="mb-8">
        <div className="flex items-center gap-4 mb-6">
          <Link href="/dashboard/clients" className="text-muted-foreground hover:text-foreground text-sm">
            ← Clients
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
            <span className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Téléphone</span>
            <p className="mt-1 text-sm text-foreground">
              {String(item.phone ?? '')}
            </p>
          </div>
        </div>
      </div>

      {/* ── Véhicules ── */}
      <section className="mb-8">
        <h2 className="text-lg font-semibold text-foreground mb-4">Véhicules</h2>

        {/* Liste */}
        {vehicleList.length === 0 ? (
          <p className="text-muted-foreground text-sm py-4 text-center">Aucun élément pour l'instant.</p>
        ) : (
          <ul className="space-y-3 mb-6">
            {vehicleList.map(c => (
              <li key={c.id} className="bg-card rounded-lg border border-border p-4 flex items-start justify-between gap-4">
                <div className="flex-1 space-y-1">
                  <p className="text-sm text-foreground">{String(c.brand ?? '')}</p>
                  <p className="text-sm text-foreground">{String(c.model ?? '')}</p>
                  <p className="text-sm text-foreground">{String(c.licensePlate ?? '')}</p>
                </div>
                <div className="flex shrink-0 gap-2 items-center">
                  <Link href={`/dashboard/vehicles/${c.id}`} className="text-xs text-primary border border-primary rounded px-2 py-1 hover:bg-primary/10">
                    Voir
                  </Link>
                  <button
                    type="button"
                    onClick={() => handleDeleteVehicle(c.id)}
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
        {vehicleError && (
          <p className="mb-3 text-sm text-red-600 bg-red-50 px-4 py-2 rounded">{vehicleError}</p>
        )}
        <form action={vehicleFormAction} className="bg-muted rounded-lg border border-border p-4 space-y-3">
          <div>
            <label htmlFor="vehicle_brand" className="block text-xs font-medium text-foreground mb-1">
              Marque <span className="text-red-500">*</span>            </label>
            <input
              type="text"
              id="vehicle_brand"
              name="brand"
required              className="w-full px-3 py-2 border border-border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>
          <div>
            <label htmlFor="vehicle_model" className="block text-xs font-medium text-foreground mb-1">
              Modèle <span className="text-red-500">*</span>            </label>
            <input
              type="text"
              id="vehicle_model"
              name="model"
required              className="w-full px-3 py-2 border border-border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>
          <div>
            <label htmlFor="vehicle_licensePlate" className="block text-xs font-medium text-foreground mb-1">
              Plaque d'immatriculation <span className="text-red-500">*</span>            </label>
            <input
              type="text"
              id="vehicle_licensePlate"
              name="licensePlate"
required              className="w-full px-3 py-2 border border-border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>
          <button
            type="submit"
            disabled={vehiclePending}
            className="px-4 py-2 bg-primary text-white rounded-md text-sm font-medium hover:bg-primary/85 disabled:opacity-50"
          >
            {vehiclePending ? 'En cours…' : 'Ajouter'}
          </button>
        </form>
      </section>
    </main>
  )
}
