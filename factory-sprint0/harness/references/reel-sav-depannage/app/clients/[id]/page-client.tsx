'use client'

import { useState, useActionState } from 'react'
import Link from 'next/link'
import type { SerializedClient } from '@/lib/types'
import type { SerializedMachine } from '@/lib/types'
import { createMachine, deleteMachine } from '@/app/machines/actions'

interface ClientsIdClientProps {
  item: SerializedClient
}

export default function ClientsIdClient({ item }: ClientsIdClientProps) {
  const [machineList, setMachineList] = useState<SerializedMachine[]>(
    (item.machines as SerializedMachine[] | undefined) ?? []
  )

  const [machineError, machineFormAction, machinePending] = useActionState(
    async (_prev: unknown, formData: FormData) => {
      formData.set('clientId', item.id)
      try {
        await createMachine(formData)
        return null
      } catch (e) {
        return (e as Error).message
      }
    },
    null,
  )

  const handleDeleteMachine = async (id: string) => {
    if (!confirm('Supprimer cet élément ?')) return
    await deleteMachine(id)
    setMachineList(prev => prev.filter(c => c.id !== id))
  }

  return (
    <main className="container mx-auto p-4 max-w-4xl">
      {/* ── Détail Client ── */}
      <div className="mb-8">
        <div className="flex items-center gap-4 mb-6">
          <Link href="/clients" className="text-muted-foreground hover:text-foreground text-sm">
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
            <span className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Email</span>
            <p className="mt-1 text-sm text-foreground">
              {String(item.email ?? '')}
            </p>
          </div>
          <div>
            <span className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Adresse</span>
            <p className="mt-1 text-sm text-foreground">
              {String(item.address ?? '')}
            </p>
          </div>
        </div>
      </div>

      {/* ── Machines ── */}
      <section className="mb-8">
        <h2 className="text-lg font-semibold text-foreground mb-4">Machines</h2>

        {/* Liste */}
        {machineList.length === 0 ? (
          <p className="text-muted-foreground text-sm py-4 text-center">Aucun élément pour l'instant.</p>
        ) : (
          <ul className="space-y-3 mb-6">
            {machineList.map(c => (
              <li key={c.id} className="bg-card rounded-lg border border-border p-4 flex items-start justify-between gap-4">
                <div className="flex-1 space-y-1">
                  <p className="text-sm text-foreground">{String(c.model ?? '')}</p>
                  <p className="text-sm text-foreground">{String(c.serialNumber ?? '')}</p>
                  <p className="text-sm text-foreground">{String(c.socket ?? '')}</p>
                </div>
                <div className="flex shrink-0 gap-2 items-center">
                  <Link href={`/machines/${c.id}`} className="text-xs text-primary border border-primary rounded px-2 py-1 hover:bg-primary/10">
                    Voir
                  </Link>
                  <button
                    type="button"
                    onClick={() => handleDeleteMachine(c.id)}
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
        {machineError && (
          <p className="mb-3 text-sm text-red-600 bg-red-50 px-4 py-2 rounded">{machineError}</p>
        )}
        <form action={machineFormAction} className="bg-muted rounded-lg border border-border p-4 space-y-3">
          <div>
            <label htmlFor="machine_model" className="block text-xs font-medium text-foreground mb-1">
              Modèle <span className="text-red-500">*</span>            </label>
            <input
              type="text"
              id="machine_model"
              name="model"
required              className="w-full px-3 py-2 border border-border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>
          <div>
            <label htmlFor="machine_serialNumber" className="block text-xs font-medium text-foreground mb-1">
              Numéro de série <span className="text-red-500">*</span>            </label>
            <input
              type="text"
              id="machine_serialNumber"
              name="serialNumber"
required              className="w-full px-3 py-2 border border-border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>
          <div>
            <label htmlFor="machine_socket" className="block text-xs font-medium text-foreground mb-1">
              Socket <span className="text-red-500">*</span>            </label>
            <select
              id="machine_socket"
              name="socket"
              className="w-full px-3 py-2 border border-border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            >
              <option value="">Sélectionner…</option>
              <option value="478">478</option>
              <option value="754">754</option>
              <option value="775">775</option>
              <option value="am2">AM2</option>
            </select>
          </div>
          <button
            type="submit"
            disabled={machinePending}
            className="px-4 py-2 bg-primary text-white rounded-md text-sm font-medium hover:bg-primary/85 disabled:opacity-50"
          >
            {machinePending ? 'En cours…' : 'Ajouter'}
          </button>
        </form>
      </section>
    </main>
  )
}
