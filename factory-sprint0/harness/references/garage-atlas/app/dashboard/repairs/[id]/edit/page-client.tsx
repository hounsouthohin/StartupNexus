'use client'

import { useActionState } from 'react'
import Link from 'next/link'
import type { SerializedRepair } from '@/lib/types'
import type { SerializedVehicle } from '@/lib/types'
import { updateRepair } from '@/app/dashboard/repairs/actions'


interface RepairEditClientProps {
  item: SerializedRepair
  vehicleOptions: SerializedVehicle[]
}

export default function RepairEditClient({ item, vehicleOptions }: RepairEditClientProps) {
  const [error, formAction, isPending] = useActionState(
    async (_prev: unknown, formData: FormData) => {
      try { await updateRepair.bind(null, item.id)(formData); return null }
      catch (e) { return (e as Error).message }
    },
    null,
  )

  return (
    <main className="container mx-auto p-4 max-w-xl">
      <div className="flex items-center gap-3 mb-6">
        <Link href="/dashboard/repairs" className="text-muted-foreground hover:text-foreground">←</Link>
        <h1 className="text-2xl font-bold text-foreground">Modifier Réparation</h1>
      </div>

      {error && <p className="mb-4 text-sm text-red-600 bg-red-50 px-4 py-2 rounded">{error}</p>}

      <form action={formAction} className="space-y-4 bg-card rounded-lg shadow-sm border border-border p-4">
        <div>
          <label htmlFor="description" className="block text-sm font-medium text-foreground mb-1">
            Description
          </label>
          <textarea
            id="description"
            name="description"
            rows={4}
            defaultValue={item.description ?? ''}
            className="w-full px-3 py-2 border border-border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary disabled:bg-muted disabled:text-muted-foreground"
          />
        </div>

        <div>
          <label htmlFor="vehicleId" className="block text-sm font-medium text-foreground mb-1">
            Vehicle
          </label>
          <select
            id="vehicleId"
            name="vehicleId"
            defaultValue={item.vehicleId ?? ''}
            className="w-full px-3 py-2 border border-border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary disabled:bg-muted disabled:text-muted-foreground"
          >
            <option value="">Sélectionner…</option>
            {vehicleOptions.map(opt => (
              <option key={opt.id} value={opt.id}>{String(opt.brand ?? opt.id)}</option>
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
            href="/dashboard/repairs"
            className="px-6 py-2 border border-border rounded-md text-sm font-medium text-foreground hover:bg-muted/50"
          >
            Annuler
          </Link>
        </div>
      </form>
    </main>
  )
}
