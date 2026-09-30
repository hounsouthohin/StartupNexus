'use client'

import Link from 'next/link'
import type { SerializedRunEvent } from '@/lib/types'
import { formatDate } from '@/lib/utils'

const FIELD_VALUE_LABELS: Record<string, Record<string, string>> = {"status": {"ouverte": "Ouverte", "complete": "Complète", "annulee": "Annulée"}};

interface RunEventsIdClientProps {
  item: SerializedRunEvent
}

export default function RunEventsIdClient({ item }: RunEventsIdClientProps) {

  return (
    <main className="container mx-auto p-6 max-w-2xl">
      <div className="flex items-center gap-3 mb-6">
        <Link href="/run-events" className="text-muted-foreground hover:text-foreground">←</Link>
        <h1 className="text-2xl font-bold text-foreground">{String(item.title ?? 'Sortie')}</h1>
      </div>

      <div className="bg-card rounded-lg shadow-sm border border-border p-6 mb-4">
        <p className="text-sm font-medium text-muted-foreground mb-2">Description du parcours</p>
        <p className="text-foreground leading-relaxed whitespace-pre-wrap">{String(item.description ?? '')}</p>
      </div>

      <div className="bg-card rounded-lg shadow-sm border border-border overflow-hidden">
        <dl className="divide-y divide-border">
          <div className="px-6 py-4 grid grid-cols-3 gap-4">
            <dt className="text-sm font-medium text-muted-foreground">Date et Heure</dt>
            <dd className="text-sm text-foreground col-span-2">
              {formatDate(item.dateTime)}
            </dd>
          </div>
          <div className="px-6 py-4 grid grid-cols-3 gap-4">
            <dt className="text-sm font-medium text-muted-foreground">Lieu de départ</dt>
            <dd className="text-sm text-foreground col-span-2">
              {String(item.location ?? '—')}
            </dd>
          </div>
          <div className="px-6 py-4 grid grid-cols-3 gap-4">
            <dt className="text-sm font-medium text-muted-foreground">Distance (km)</dt>
            <dd className="text-sm text-foreground col-span-2">
              {String(item.distance ?? '—')}
            </dd>
          </div>
          <div className="px-6 py-4 grid grid-cols-3 gap-4">
            <dt className="text-sm font-medium text-muted-foreground">Statut</dt>
            <dd className="text-sm text-foreground col-span-2">
              {(FIELD_VALUE_LABELS['status'] ?? {})[String(item.status)] ?? String(item.status ?? '—')}
            </dd>
          </div>
        </dl>
      </div>


      <div className="mt-6 flex gap-3">
        <Link
          href="/run-events"
          className="px-4 py-2 border border-border rounded-md text-sm font-medium text-foreground hover:bg-muted/50"
        >
          Retour
        </Link>
      </div>
    </main>
  )
}
