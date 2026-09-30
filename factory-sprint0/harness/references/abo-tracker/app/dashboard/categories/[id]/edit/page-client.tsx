'use client'

import { useActionState } from 'react'
import Link from 'next/link'
import type { SerializedCategory } from '@/lib/types'
import { updateCategory } from '@/app/dashboard/categories/actions'


interface CategoryEditClientProps {
  item: SerializedCategory
}

export default function CategoryEditClient({ item }: CategoryEditClientProps) {
  const [error, formAction, isPending] = useActionState(
    async (_prev: unknown, formData: FormData) => {
      try { await updateCategory.bind(null, item.id)(formData); return null }
      catch (e) { return (e as Error).message }
    },
    null,
  )

  return (
    <main className="container mx-auto p-6 max-w-xl">
      <div className="flex items-center gap-3 mb-6">
        <Link href="/dashboard/categories" className="text-muted-foreground hover:text-foreground">←</Link>
        <h1 className="text-2xl font-bold text-foreground">Modifier Catégorie</h1>
      </div>

      {error && <p className="mb-4 text-sm text-red-600 bg-red-50 px-4 py-2 rounded">{error}</p>}

      <form action={formAction} className="space-y-4 bg-card rounded-lg shadow-sm border border-border p-6">
        <div>
          <label htmlFor="name" className="block text-sm font-medium text-foreground mb-1">
            Nom
          </label>
          <input
            type="text"
            id="name"
            name="name"
            defaultValue={item.name != null ? String(item.name) : ''}
            className="w-full px-3 py-2 border border-border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary disabled:bg-muted disabled:text-muted-foreground"
          />
        </div>
        <div>
          <label htmlFor="description" className="block text-sm font-medium text-foreground mb-1">
            Description
          </label>
          <textarea
            id="description"
            name="description"
            rows={4}
            defaultValue={item.description ?? ''}
            className="w-full px-3 py-2 border border-border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary disabled:bg-muted disabled:text-muted-foreground"
          />
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
            href="/dashboard/categories"
            className="px-6 py-2 border border-border rounded-md text-sm font-medium text-foreground hover:bg-muted/50"
          >
            Annuler
          </Link>
        </div>
      </form>
    </main>
  )
}
