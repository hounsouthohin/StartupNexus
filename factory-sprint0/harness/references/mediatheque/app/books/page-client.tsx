'use client'

import Link from 'next/link'
import type { SerializedBook } from '@/lib/types'
import { formatDate } from '@/lib/utils'

interface BooksClientProps {
  items: SerializedBook[]
}

export default function BooksClient({ items }: BooksClientProps) {
  return (
    <main className="container mx-auto p-8">
      <h1 className="text-3xl font-bold text-foreground mb-8">Ouvrages</h1>

      {items.length === 0 ? (
        <div className="text-center py-16 text-muted-foreground">
          <p className="text-lg">Aucun ouvrage disponible pour le moment.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {items.map(item => (
            <div
              key={item.id}
              className="bg-muted/30 rounded-lg overflow-hidden transition-all duration-300 ease-out hover:shadow-md group"
            >
              <div className="p-5">
                <h2 className="text-lg font-semibold text-foreground group-hover:text-primary transition-all duration-300 ease-out mb-2 line-clamp-2">
                  {String(item.title ?? '—')}
                </h2>
                <p className="text-sm text-muted-foreground mb-1 line-clamp-3">
{String(item.author ?? '—')}                </p>
                <p className="text-sm text-muted-foreground mb-1 line-clamp-3">
{String(item.genre ?? '—')}                </p>
              </div>
              <div className="px-5 pb-5">
                <Link
                  href={`/books/${item.id}`}
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
