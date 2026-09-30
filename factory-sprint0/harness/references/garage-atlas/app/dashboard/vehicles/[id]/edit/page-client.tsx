'use client'

import { useActionState } from 'react'
import Link from 'next/link'
import type { SerializedVehicle } from '@/lib/types'
import type { SerializedClient } from '@/lib/types'
import { updateVehicle } from '@/app/dashboard/vehicles/actions'


interface VehicleEditClientProps {
  item: SerializedVehicle
  clientOptions: SerializedClient[]
}

export default function VehicleEditClient({ item, clientOptions }: VehicleEditClientProps) {
  const [error, formAction, isPending] = useActionState(
    async (_prev: unknown, formData: FormData) => {
      try { await updateVehicle.bind(null, item.id)(formData); return null }
      catch (e) { return (e as Error).message }
    },
    null,
  )

  return (
    <main className="container mx-auto p-4 max-w-xl">
      <div className="flex items-center gap-3 mb-6">
        <Link href="/dashboard/vehicles" className="text-muted-foreground hover:text-foreground">←</Link>
        <h1 className="text-2xl font-bold text-foreground">Modifier Véhicule</h1>
      </div>

      {error && <p className="mb-4 text-sm text-red-600 bg-red-50 px-4 py-2 rounded">{error}</p>}

      <form action={formAction} className="space-y-4 bg-card rounded-lg shadow-sm border border-border p-4">
        <div>
          <label htmlFor="brand" className="block text-sm font-medium text-foreground mb-1">
            Marque
          </label>
          <input
            type="text"
            id="brand"
            name="brand"
            defaultValue={item.brand != null ? String(item.brand) : ''}
            className="w-full px-3 py-2 border border-border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary disabled:bg-muted disabled:text-muted-foreground"
          />
        </div>
        <div>
          <label htmlFor="model" className="block text-sm font-medium text-foreground mb-1">
            Modèle
          </label>
          <input
            type="text"
            id="model"
            name="model"
            defaultValue={item.model != null ? String(item.model) : ''}
            className="w-full px-3 py-2 border border-border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary disabled:bg-muted disabled:text-muted-foreground"
          />
        </div>
        <div>
          <label htmlFor="licensePlate" className="block text-sm font-medium text-foreground mb-1">
            Plaque d'immatriculation
          </label>
          <input
            type="text"
            id="licensePlate"
            name="licensePlate"
            defaultValue={item.licensePlate != null ? String(item.licensePlate) : ''}
            className="w-full px-3 py-2 border border-border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary disabled:bg-muted disabled:text-muted-foreground"
          />
        </div>

        <div>
          <label htmlFor="clientId" className="block text-sm font-medium text-foreground mb-1">
            Client
          </label>
          <select
            id="clientId"
            name="clientId"
            defaultValue={item.clientId ?? ''}
            className="w-full px-3 py-2 border border-border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary disabled:bg-muted disabled:text-muted-foreground"
          >
            <option value="">Sélectionner…</option>
            {clientOptions.map(opt => (
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
            href="/dashboard/vehicles"
            className="px-6 py-2 border border-border rounded-md text-sm font-medium text-foreground hover:bg-muted/50"
          >
            Annuler
          </Link>
        </div>
      </form>
    </main>
  )
}
