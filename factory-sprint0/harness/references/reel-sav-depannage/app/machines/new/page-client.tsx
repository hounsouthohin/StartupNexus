'use client'

import { useActionState } from 'react'
import Link from 'next/link'
import { createMachine } from '@/app/machines/actions'
import type { SerializedClient } from '@/lib/types'

interface MachinesNewClientProps {
  clientOptions: SerializedClient[]
}

export default function MachinesNewClient({ clientOptions }: MachinesNewClientProps) {
  const [error, formAction, isPending] = useActionState(
    async (_prev: unknown, formData: FormData) => {
      try { await createMachine(formData); return null }
      catch (e) { return (e as Error).message }
    },
    null,
  )

  return (
    <main className="container mx-auto p-4 max-w-xl">
      <div className="flex items-center gap-3 mb-6">
        <Link href="/machines" className="text-muted-foreground hover:text-foreground">←</Link>
        <h1 className="text-2xl font-bold text-foreground">Créer Machine</h1>
      </div>

      {error && <p className="mb-4 text-sm text-red-600 bg-red-50 px-4 py-2 rounded">{error}</p>}

      <form action={formAction} className="space-y-4 bg-card rounded-lg shadow-sm border border-border p-4">
        <div>
          <label htmlFor="model" className="block text-sm font-medium text-foreground mb-1">
            Modèle <span className="text-red-500">*</span>          </label>
          <input
            type="text"
            id="model"
            name="model"
required             className="w-full px-3 py-2 border border-border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary"
          />
        </div>
        <div>
          <label htmlFor="serialNumber" className="block text-sm font-medium text-foreground mb-1">
            Numéro de série <span className="text-red-500">*</span>          </label>
          <input
            type="text"
            id="serialNumber"
            name="serialNumber"
required             className="w-full px-3 py-2 border border-border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary"
          />
        </div>
        <div>
          <label htmlFor="socket" className="block text-sm font-medium text-foreground mb-1">
            Socket <span className="text-red-500">*</span>          </label>
          <select
            id="socket"
            name="socket"
required            className="w-full px-3 py-2 border border-border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary"
          >
            <option value="">Sélectionner…</option>
            <option value="478">478</option>
            <option value="754">754</option>
            <option value="775">775</option>
            <option value="am2">AM2</option>
          </select>
        </div>

        <div>
          <label htmlFor="clientId" className="block text-sm font-medium text-foreground mb-1">
            Client
          </label>
          <select
            id="clientId"
            name="clientId"
            required
            className="w-full px-3 py-2 border border-border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary"
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
            {isPending ? 'En cours…' : 'Créer'}
          </button>
          <Link
            href="/machines"
            className="px-6 py-2 border border-border rounded-md text-sm font-medium text-foreground hover:bg-muted/50"
          >
            Annuler
          </Link>
        </div>
      </form>
    </main>
  )
}
