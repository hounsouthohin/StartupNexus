'use client'

import Link from 'next/link'
import type { SerializedWorkshop } from '@/lib/types'
import { formatDate } from '@/lib/utils'
import { formatCurrency } from '@/lib/utils'

interface WorkshopsIdClientProps {
  item: SerializedWorkshop
}

export default function WorkshopsIdClient({ item }: WorkshopsIdClientProps) {

  return (
    <main className="container mx-auto p-6 max-w-2xl">
      <div className="flex items-center gap-3 mb-6">
        <Link href="/workshops" className="text-muted-foreground hover:text-foreground">←</Link>
        <h1 className="text-2xl font-bold text-foreground">{String(item.title ?? 'Atelier')}</h1>
      </div>

      {(item.domains ?? []).length > 0 && (
        <div className="flex flex-wrap gap-2 mb-4">
          {(item.domains ?? []).map(rel => (
            <span key={rel.id} className="inline-flex px-2 py-0.5 rounded-full text-xs font-medium bg-primary/10 text-primary">
              {String(rel.name ?? '')}
            </span>
          ))}
        </div>
      )}

      <div className="bg-card rounded-lg border-2 border-border p-6 mb-4">
        <p className="text-sm font-medium text-muted-foreground mb-2">Description</p>
        <p className="text-foreground leading-relaxed whitespace-pre-wrap">{String(item.description ?? '')}</p>
      </div>

      <div className="bg-card rounded-lg border-2 border-border overflow-hidden">
        <dl className="divide-y divide-border">
          <div className="px-6 py-4 grid grid-cols-3 gap-4">
            <dt className="text-sm font-medium text-muted-foreground">Durée</dt>
            <dd className="text-sm text-foreground col-span-2">
              {String(item.duration ?? '—')}
            </dd>
          </div>
          <div className="px-6 py-4 grid grid-cols-3 gap-4">
            <dt className="text-sm font-medium text-muted-foreground">Prix</dt>
            <dd className="text-sm text-foreground col-span-2">
              {formatCurrency(item.price)}
            </dd>
          </div>
        </dl>
      </div>


      <div className="mt-6 flex gap-3">
        <Link
          href="/workshops"
          className="px-4 py-2 border border-border rounded-md text-sm font-medium text-foreground hover:bg-muted/50"
        >
          Retour
        </Link>
      </div>
    </main>
  )
}
