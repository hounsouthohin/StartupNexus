'use client'

import { useActionState } from 'react'
import Link from 'next/link'
import type { SerializedRecipe } from '@/lib/types'
import type { SerializedTag } from '@/lib/types'
import { updateRecipe } from '@/app/dashboard/recipes/actions'


interface RecipeEditClientProps {
  item: SerializedRecipe
  tagOptions: SerializedTag[]
}

export default function RecipeEditClient({ item, tagOptions }: RecipeEditClientProps) {
  const [error, formAction, isPending] = useActionState(
    async (_prev: unknown, formData: FormData) => {
      try { await updateRecipe.bind(null, item.id)(formData); return null }
      catch (e) { return (e as Error).message }
    },
    null,
  )

  return (
    <main className="container mx-auto p-8 max-w-xl">
      <div className="flex items-center gap-3 mb-6">
        <Link href="/dashboard/recipes" className="text-muted-foreground hover:text-foreground">←</Link>
        <h1 className="text-2xl font-bold text-foreground">Modifier Recette</h1>
      </div>

      {error && <p className="mb-4 text-sm text-red-600 bg-red-50 px-4 py-2 rounded">{error}</p>}

      <form action={formAction} className="space-y-4 bg-card rounded-lg shadow-sm border border-border p-8">
        <div>
          <label htmlFor="title" className="block text-sm font-medium text-foreground mb-1">
            Titre
          </label>
          <input
            type="text"
            id="title"
            name="title"
            defaultValue={item.title != null ? String(item.title) : ''}
            className="w-full px-3 py-2 border border-border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary disabled:bg-muted disabled:text-muted-foreground"
          />
        </div>
        <div>
          <label htmlFor="instructions" className="block text-sm font-medium text-foreground mb-1">
            Instructions
          </label>
          <textarea
            id="instructions"
            name="instructions"
            rows={12}
            defaultValue={item.instructions ?? ''}
            className="w-full px-3 py-2 border border-border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary disabled:bg-muted disabled:text-muted-foreground"
          />
        </div>
        <div>
          <label htmlFor="preparationTime" className="block text-sm font-medium text-foreground mb-1">
            Temps de préparation
          </label>
          <input
            type="number"
            id="preparationTime"
            name="preparationTime"
            defaultValue={item.preparationTime != null ? String(item.preparationTime) : ''}
step="any"             className="w-full px-3 py-2 border border-border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary disabled:bg-muted disabled:text-muted-foreground"
          />
        </div>
        <div>
          <label htmlFor="difficulty" className="block text-sm font-medium text-foreground mb-1">
            Difficulté
          </label>
          <select
            id="difficulty"
            name="difficulty"
            defaultValue={item.difficulty ?? ''}
            className="w-full px-3 py-2 border border-border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary disabled:bg-muted disabled:text-muted-foreground"
          >
            <option value="">Sélectionner…</option>
            <option value="facile">Facile</option>
            <option value="moyenne">Moyenne</option>
            <option value="difficile">Difficile</option>
          </select>
        </div>
        <div>
          <label htmlFor="published" className="block text-sm font-medium text-foreground mb-1">
            Publié
          </label>
          <input
            type="checkbox"
            id="published"
            name="published"
            value="true"
            defaultChecked={Boolean(item.published)}
            className="h-4 w-4 text-primary border-border rounded disabled:opacity-50"
          />
        </div>


        <div>
          <span className="block text-sm font-medium text-foreground mb-1">Tags</span>
          <div className="max-h-40 overflow-y-auto border border-border rounded-md p-3 space-y-2">
            {tagOptions.length === 0 ? (
              <p className="text-sm text-muted-foreground">Aucun élément disponible.</p>
            ) : tagOptions.map(opt => (
              <label key={opt.id} className="flex items-center gap-2 text-sm text-foreground">
                <input
                  type="checkbox"
                  name="tagIds"
                  value={opt.id}
                  defaultChecked={(item.tags ?? []).some(rel => rel.id === opt.id)}
                  className="h-4 w-4 text-primary border-border rounded"
                />
                <span>{String(opt.name ?? opt.id)}</span>
              </label>
            ))}
          </div>
        </div>

        <div className="flex gap-3 pt-2">
          <button
            type="submit"
            disabled={isPending}
            className="flex-1 px-6 py-2 bg-primary text-white rounded-md text-sm font-medium hover:bg-primary/85 disabled:opacity-50"
          >
            {isPending ? 'En cours…' : 'Enregistrer'}
          </button>
          <Link
            href="/dashboard/recipes"
            className="px-6 py-2 border border-border rounded-md text-sm font-medium text-foreground hover:bg-muted/50"
          >
            Annuler
          </Link>
        </div>
      </form>
    </main>
  )
}
