'use client'

import { useState, useActionState } from 'react'
import Link from 'next/link'
import type { SerializedMachine } from '@/lib/types'
import type { SerializedIntervention } from '@/lib/types'
import { createIntervention, deleteIntervention } from '@/app/interventions/actions'

interface MachinesIdClientProps {
  item: SerializedMachine
}

export default function MachinesIdClient({ item }: MachinesIdClientProps) {
  const [interventionList, setInterventionList] = useState<SerializedIntervention[]>(
    (item.interventions as SerializedIntervention[] | undefined) ?? []
  )

  const [interventionError, interventionFormAction, interventionPending] = useActionState(
    async (_prev: unknown, formData: FormData) => {
      formData.set('machineId', item.id)
      try {
        await createIntervention(formData)
        return null
      } catch (e) {
        return (e as Error).message
      }
    },
    null,
  )

  const handleDeleteIntervention = async (id: string) => {
    if (!confirm('Supprimer cet élément ?')) return
    await deleteIntervention(id)
    setInterventionList(prev => prev.filter(c => c.id !== id))
  }

  return (
    <main className="container mx-auto p-4 max-w-4xl">
      {/* ── Détail Machine ── */}
      <div className="mb-8">
        <div className="flex items-center gap-4 mb-6">
          <Link href="/machines" className="text-muted-foreground hover:text-foreground text-sm">
            ← Machines
          </Link>
        </div>
        <div className="bg-card rounded-lg shadow-sm border border-border p-4 space-y-3">
          <div>
            <span className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Modèle</span>
            <p className="mt-1 text-sm text-foreground">
              {String(item.model ?? '')}
            </p>
          </div>
          <div>
            <span className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Numéro de série</span>
            <p className="mt-1 text-sm text-foreground">
              {String(item.serialNumber ?? '')}
            </p>
          </div>
          <div>
            <span className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Socket</span>
            <p className="mt-1 text-sm text-foreground">
              {({"478": "478", "754": "754", "775": "775", "am2": "AM2"} as Record<string, string>)[String(item.socket ?? '')] ?? String(item.socket ?? '')}
            </p>
          </div>
        </div>
      </div>

      {/* ── Interventions ── */}
      <section className="mb-8">
        <h2 className="text-lg font-semibold text-foreground mb-4">Interventions</h2>

        {/* Liste */}
        {interventionList.length === 0 ? (
          <p className="text-muted-foreground text-sm py-4 text-center">Aucun élément pour l'instant.</p>
        ) : (
          <ul className="space-y-3 mb-6">
            {interventionList.map(c => (
              <li key={c.id} className="bg-card rounded-lg border border-border p-4 flex items-start justify-between gap-4">
                <div className="flex-1 space-y-1">
                  <p className="text-sm text-foreground">{String(c.date ?? '')}</p>
                  <p className="text-sm text-foreground">{String(c.status ?? '')}</p>
                </div>
                <div className="flex shrink-0 gap-2 items-center">
                  <Link href={`/interventions/${c.id}`} className="text-xs text-primary border border-primary rounded px-2 py-1 hover:bg-primary/10">
                    Voir
                  </Link>
                  <button
                    type="button"
                    onClick={() => handleDeleteIntervention(c.id)}
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
        {interventionError && (
          <p className="mb-3 text-sm text-red-600 bg-red-50 px-4 py-2 rounded">{interventionError}</p>
        )}
        <form action={interventionFormAction} className="bg-muted rounded-lg border border-border p-4 space-y-3">
          <div>
            <label htmlFor="intervention_date" className="block text-xs font-medium text-foreground mb-1">
              Date <span className="text-red-500">*</span>            </label>
            <input
              type="datetime-local"
              id="intervention_date"
              name="date"
required              className="w-full px-3 py-2 border border-border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>
          <div>
            <label htmlFor="intervention_status" className="block text-xs font-medium text-foreground mb-1">
              Statut            </label>
            <select
              id="intervention_status"
              name="status"
              className="w-full px-3 py-2 border border-border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            >
              <option value="">Sélectionner…</option>
              <option value="ouverte">Ouverte</option>
              <option value="en_cours">En cours</option>
              <option value="cloturee">Clôturée</option>
              <option value="payee">Payée</option>
            </select>
          </div>
          <button
            type="submit"
            disabled={interventionPending}
            className="px-4 py-2 bg-primary text-white rounded-md text-sm font-medium hover:bg-primary/85 disabled:opacity-50"
          >
            {interventionPending ? 'En cours…' : 'Ajouter'}
          </button>
        </form>
      </section>
    </main>
  )
}
