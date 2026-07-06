'use client'

import { useState, useActionState } from 'react'
import Link from 'next/link'
import type { SerializedRunEvent } from '@/lib/types'
import type { SerializedParticipant } from '@/lib/types'
import { createParticipant, deleteParticipant } from '@/app/participants/actions'

interface DashboardRunEventsIdClientProps {
  item: SerializedRunEvent
}

export default function DashboardRunEventsIdClient({ item }: DashboardRunEventsIdClientProps) {
  const [participantList, setParticipantList] = useState<SerializedParticipant[]>(
    (item.participants as SerializedParticipant[] | undefined) ?? []
  )

  const [participantError, participantFormAction, participantPending] = useActionState(
    async (_prev: unknown, formData: FormData) => {
      formData.set('runEventId', item.id)
      try {
        await createParticipant(formData)
        return null
      } catch (e) {
        return (e as Error).message
      }
    },
    null,
  )

  const handleDeleteParticipant = async (id: string) => {
    if (!confirm('Supprimer cet élément ?')) return
    await deleteParticipant(id)
    setParticipantList(prev => prev.filter(c => c.id !== id))
  }

  return (
    <main className="container mx-auto p-6 max-w-4xl">
      {/* ── Détail RunEvent ── */}
      <div className="mb-8">
        <div className="flex items-center gap-4 mb-6">
          <Link href="/dashboard/run-events" className="text-muted-foreground hover:text-foreground text-sm">
            ← RunEvents
          </Link>
        </div>
        <div className="bg-card rounded-lg shadow-sm border border-border p-6 space-y-3">
          <div>
            <span className="text-xs font-medium text-muted-foreground uppercase tracking-wide">title</span>
            <p className="mt-1 text-sm text-foreground">
              {String(item.title ?? '')}
            </p>
          </div>
        </div>
      </div>

      {/* ── Participants ── */}
      <section className="mb-8">
        <h2 className="text-lg font-semibold text-foreground mb-4">Participants</h2>

        {/* Liste */}
        {participantList.length === 0 ? (
          <p className="text-muted-foreground text-sm py-4 text-center">Aucun élément pour l'instant.</p>
        ) : (
          <ul className="space-y-3 mb-6">
            {participantList.map(c => (
              <li key={c.id} className="bg-card rounded-lg border border-border p-4 flex items-start justify-between gap-4">
                <div className="flex-1 space-y-1">
                  <p className="text-sm text-foreground">{String(c.id ?? '')}</p>
                </div>
                <div className="flex shrink-0 gap-2 items-center">
                  <button
                    type="button"
                    onClick={() => handleDeleteParticipant(c.id)}
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
        {participantError && (
          <p className="mb-3 text-sm text-red-600 bg-red-50 px-4 py-2 rounded">{participantError}</p>
        )}
        <form action={participantFormAction} className="bg-muted rounded-lg border border-border p-4 space-y-3">
          <button
            type="submit"
            disabled={participantPending}
            className="px-4 py-2 bg-primary text-white rounded-md text-sm font-medium hover:bg-primary/85 disabled:opacity-50"
          >
            {participantPending ? 'En cours…' : 'Ajouter'}
          </button>
        </form>
      </section>
    </main>
  )
}
