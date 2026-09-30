'use client'

import Link from 'next/link'
import type { SerializedRecipe } from '@/lib/types'
import { formatDate } from '@/lib/utils'

const FIELD_VALUE_LABELS: Record<string, Record<string, string>> = {"difficulty": {"facile": "Facile", "moyenne": "Moyenne", "difficile": "Difficile"}};

interface RecipesSlugClientProps {
  item: SerializedRecipe
}

export default function RecipesSlugClient({ item }: RecipesSlugClientProps) {

  return (
    <main className="container mx-auto p-8 max-w-2xl">
      <div className="flex items-center gap-3 mb-6">
        <Link href="/recipes" className="text-muted-foreground hover:text-foreground">←</Link>
        <h1 className="text-2xl font-bold text-foreground">{String(item.title ?? 'Recette')}</h1>
      </div>

      {(item.tags ?? []).length > 0 && (
        <div className="flex flex-wrap gap-2 mb-4">
          {(item.tags ?? []).map(rel => (
            <span key={rel.id} className="inline-flex px-2 py-0.5 rounded-full text-xs font-medium bg-primary/10 text-primary">
              {String(rel.name ?? '')}
            </span>
          ))}
        </div>
      )}

      <div className="bg-card rounded-lg shadow-sm border border-border p-6 mb-4">
        <p className="text-sm font-medium text-muted-foreground mb-2">Instructions</p>
        <p className="text-foreground leading-relaxed whitespace-pre-wrap">{String(item.instructions ?? '')}</p>
      </div>

      <div className="bg-card rounded-lg shadow-sm border border-border overflow-hidden">
        <dl className="divide-y divide-border">
          <div className="px-6 py-4 grid grid-cols-3 gap-4">
            <dt className="text-sm font-medium text-muted-foreground">Temps de préparation</dt>
            <dd className="text-sm text-foreground col-span-2">
              {String(item.preparationTime ?? '—')}
            </dd>
          </div>
          <div className="px-6 py-4 grid grid-cols-3 gap-4">
            <dt className="text-sm font-medium text-muted-foreground">Difficulté</dt>
            <dd className="text-sm text-foreground col-span-2">
              {(FIELD_VALUE_LABELS['difficulty'] ?? {})[String(item.difficulty)] ?? String(item.difficulty ?? '—')}
            </dd>
          </div>
        </dl>
      </div>


      <div className="mt-6 flex gap-3">
        <Link
          href="/recipes"
          className="px-4 py-2 border border-border rounded-md text-sm font-medium text-foreground hover:bg-muted/50"
        >
          Retour
        </Link>
      </div>
    </main>
  )
}
