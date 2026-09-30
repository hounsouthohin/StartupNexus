'use client'

import Link from 'next/link'
import type { SerializedBook } from '@/lib/types'
import { formatDate } from '@/lib/utils'

const FIELD_VALUE_LABELS: Record<string, Record<string, string>> = {"genre": {"roman": "Roman", "essai": "Essai", "bande_dessinee": "Bande dessinée", "jeunesse": "Jeunesse"}};

interface BooksIdClientProps {
  item: SerializedBook
}

export default function BooksIdClient({ item }: BooksIdClientProps) {

  return (
    <main className="container mx-auto p-8 max-w-2xl">
      <div className="flex items-center gap-3 mb-6">
        <Link href="/books" className="text-muted-foreground hover:text-foreground">←</Link>
        <h1 className="text-2xl font-bold text-foreground">{String(item.title ?? 'Ouvrage')}</h1>
      </div>

      <div className="bg-muted/30 rounded-lg p-6 mb-4">
        <p className="text-sm font-medium text-muted-foreground mb-2">Résumé</p>
        <p className="text-foreground leading-relaxed whitespace-pre-wrap">{String(item.summary ?? '')}</p>
      </div>

      <div className="bg-muted/30 rounded-lg overflow-hidden">
        <dl className="divide-y divide-border">
          <div className="px-6 py-4 grid grid-cols-3 gap-4">
            <dt className="text-sm font-medium text-muted-foreground">Auteur</dt>
            <dd className="text-sm text-foreground col-span-2">
              {String(item.author ?? '—')}
            </dd>
          </div>
          <div className="px-6 py-4 grid grid-cols-3 gap-4">
            <dt className="text-sm font-medium text-muted-foreground">Genre</dt>
            <dd className="text-sm text-foreground col-span-2">
              {(FIELD_VALUE_LABELS['genre'] ?? {})[String(item.genre)] ?? String(item.genre ?? '—')}
            </dd>
          </div>
          <div className="px-6 py-4 grid grid-cols-3 gap-4">
            <dt className="text-sm font-medium text-muted-foreground">Année de publication</dt>
            <dd className="text-sm text-foreground col-span-2">
              {String(item.publicationYear ?? '—')}
            </dd>
          </div>
        </dl>
      </div>


      <div className="mt-6 flex gap-3">
        <Link
          href="/books"
          className="px-4 py-2 border border-border rounded-md text-sm font-medium text-foreground hover:bg-muted/50"
        >
          Retour
        </Link>
      </div>
    </main>
  )
}
