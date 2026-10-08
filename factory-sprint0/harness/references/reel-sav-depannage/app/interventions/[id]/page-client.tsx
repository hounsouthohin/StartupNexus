'use client'

import { useState, useActionState } from 'react'
import Link from 'next/link'
import type { SerializedIntervention } from '@/lib/types'
import type { SerializedAction } from '@/lib/types'
import { createAction, deleteAction } from '@/app/actions/actions'

interface InterventionsIdClientProps {
  item: SerializedIntervention
}

export default function InterventionsIdClient({ item }: InterventionsIdClientProps) {
  const [actionList, setActionList] = useState<SerializedAction[]>(
    (item.actions as SerializedAction[] | undefined) ?? []
  )

  const [actionError, actionFormAction, actionPending] = useActionState(
    async (_prev: unknown, formData: FormData) => {
      formData.set('interventionId', item.id)
      try {
        await createAction(formData)
        return null
      } catch (e) {
        return (e as Error).message
      }
    },
    null,
  )

  const handleDeleteAction = async (id: string) => {
    if (!confirm('Supprimer cet élément ?')) return
    await deleteAction(id)
    setActionList(prev => prev.filter(c => c.id !== id))
  }

  return (
    <main className="container mx-auto p-4 max-w-4xl">
      {/* ── Détail Intervention ── */}
      <div className="mb-8">
        <div className="flex items-center gap-4 mb-6">
          <Link href="/interventions" className="text-muted-foreground hover:text-foreground text-sm">
            ← Interventions
          </Link>
        </div>
        <div className="bg-card rounded-lg shadow-sm border border-border p-4 space-y-3">
          <div>
            <span className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Date</span>
            <p className="mt-1 text-sm text-foreground">
              {String(item.date ?? '')}
            </p>
          </div>
          <div>
            <span className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Statut</span>
            <p className="mt-1 text-sm text-foreground">
              {({"cloturee": "Cl\u00f4tur\u00e9e", "en_cours": "En cours", "ouverte": "Ouverte", "payee": "Pay\u00e9e"} as Record<string, string>)[String(item.status ?? '')] ?? String(item.status ?? '')}
            </p>
          </div>
        </div>
      </div>

      {/* ── Actions ── */}
      <section className="mb-8">
        <h2 className="text-lg font-semibold text-foreground mb-4">Actions</h2>

        {/* Liste */}
        {actionList.length === 0 ? (
          <p className="text-muted-foreground text-sm py-4 text-center">Aucun élément pour l'instant.</p>
        ) : (
          <ul className="space-y-3 mb-6">
            {actionList.map(c => (
              <li key={c.id} className="bg-card rounded-lg border border-border p-4 flex items-start justify-between gap-4">
                <div className="flex-1 space-y-1">
                  <p className="text-sm text-foreground">{String(c.description ?? '')}</p>
                  <p className="text-sm text-foreground">{String(c.status ?? '')}</p>
                </div>
                <div className="flex shrink-0 gap-2 items-center">
                  <Link href={`/actions/${c.id}`} className="text-xs text-primary border border-primary rounded px-2 py-1 hover:bg-primary/10">
                    Voir
                  </Link>
                  <button
                    type="button"
                    onClick={() => handleDeleteAction(c.id)}
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
        {actionError && (
          <p className="mb-3 text-sm text-red-600 bg-red-50 px-4 py-2 rounded">{actionError}</p>
        )}
        <form action={actionFormAction} className="bg-muted rounded-lg border border-border p-4 space-y-3">
          <div>
            <label htmlFor="action_description" className="block text-xs font-medium text-foreground mb-1">
              Description <span className="text-red-500">*</span>            </label>
            <textarea
              id="action_description"
              name="description"
              rows={3}
required              className="w-full px-3 py-2 border border-border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>
          <div>
            <label htmlFor="action_status" className="block text-xs font-medium text-foreground mb-1">
              Statut            </label>
            <select
              id="action_status"
              name="status"
              className="w-full px-3 py-2 border border-border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            >
              <option value="">Sélectionner…</option>
              <option value="a_faire">À faire</option>
              <option value="faite">Faite</option>
            </select>
          </div>
          <button
            type="submit"
            disabled={actionPending}
            className="px-4 py-2 bg-primary text-white rounded-md text-sm font-medium hover:bg-primary/85 disabled:opacity-50"
          >
            {actionPending ? 'En cours…' : 'Ajouter'}
          </button>
        </form>
      </section>
    </main>
  )
}
