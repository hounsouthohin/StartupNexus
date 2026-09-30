'use client'

import Link from 'next/link'
import type { SerializedSpace } from '@/lib/types'
import { formatDate } from '@/lib/utils'
import { formatCurrency } from '@/lib/utils'

const FIELD_VALUE_LABELS: Record<string, Record<string, string>> = {"type": {"private_office": "Bureau privé", "meeting_room": "Salle de réunion", "flex_desk": "Poste flexible"}};

interface SpacesIdClientProps {
  item: SerializedSpace
}

export default function SpacesIdClient({ item }: SpacesIdClientProps) {

  return (
    <main className="container mx-auto p-4 max-w-2xl">
      <div className="flex items-center gap-3 mb-6">
        <Link href="/spaces" className="text-muted-foreground hover:text-foreground">←</Link>
        <h1 className="text-2xl font-bold text-foreground">{String(item.name ?? 'Espace')}</h1>
      </div>

      <div className="bg-muted/30 rounded-lg p-6 mb-4">
        <p className="text-sm font-medium text-muted-foreground mb-2">Description</p>
        <p className="text-foreground leading-relaxed whitespace-pre-wrap">{String(item.description ?? '')}</p>
      </div>

      <div className="bg-muted/30 rounded-lg overflow-hidden">
        <dl className="divide-y divide-border">
          <div className="px-6 py-4 grid grid-cols-3 gap-4">
            <dt className="text-sm font-medium text-muted-foreground">Type</dt>
            <dd className="text-sm text-foreground col-span-2">
              {(FIELD_VALUE_LABELS['type'] ?? {})[String(item.type)] ?? String(item.type ?? '—')}
            </dd>
          </div>
          <div className="px-6 py-4 grid grid-cols-3 gap-4">
            <dt className="text-sm font-medium text-muted-foreground">Capacité</dt>
            <dd className="text-sm text-foreground col-span-2">
              {String(item.capacity ?? '—')}
            </dd>
          </div>
          <div className="px-6 py-4 grid grid-cols-3 gap-4">
            <dt className="text-sm font-medium text-muted-foreground">Tarif horaire</dt>
            <dd className="text-sm text-foreground col-span-2">
              {formatCurrency(item.hourlyRate)}
            </dd>
          </div>
          <div className="px-6 py-4 grid grid-cols-3 gap-4">
            <dt className="text-sm font-medium text-muted-foreground">Adresse</dt>
            <dd className="text-sm text-foreground col-span-2">
              {String(item.address ?? '—')}
            </dd>
          </div>
        </dl>
      </div>


      <div className="mt-6 flex gap-3">
        <Link
          href="/spaces"
          className="px-4 py-2 border border-border rounded-md text-sm font-medium text-foreground hover:bg-muted/50"
        >
          Retour
        </Link>
      </div>
    </main>
  )
}
