'use client'

import Link from 'next/link'
import type { SerializedRunEvent } from '@/lib/types'
import { formatDate } from '@/lib/utils'

interface RunEventsClientProps {
  items: SerializedRunEvent[]
}

export default function RunEventsClient({ items }: RunEventsClientProps) {
  return (
    <main className="container mx-auto p-6">
      <h1 className="text-3xl font-bold text-foreground mb-8">Sorties</h1>

      {items.length === 0 ? (
        <div className="text-center py-16 text-muted-foreground">
          <p className="text-lg">Aucune sortie prévue pour le moment. Revenez bientôt pour découvrir nos prochaines courses.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {items.map(item => (
            <div
              key={item.id}
              className="bg-card rounded-lg shadow-sm border border-border overflow-hidden transition-all duration-300 ease-out hover:shadow-md group"
            >
              <div className="p-5">
                <h2 className="text-lg font-semibold text-foreground group-hover:text-primary transition-all duration-300 ease-out mb-2 line-clamp-2">
                  {String(item.title ?? '—')}
                </h2>
                <p className="text-sm text-muted-foreground mb-1 line-clamp-3">
{formatDate(item.dateTime)}                </p>
                <p className="text-sm text-muted-foreground mb-1 line-clamp-3">
{String(item.location ?? '—')}                </p>
              </div>
              <div className="px-5 pb-5">
                <Link
                  href={`/run-events/${item.id}`}
                  className="inline-flex items-center text-sm font-medium text-primary hover:underline transition-all duration-300 ease-out"
                >
                  Lire →
                </Link>
              </div>
            </div>
          ))}
        </div>
      )}
    </main>
  )
}
