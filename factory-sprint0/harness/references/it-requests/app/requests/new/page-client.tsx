'use client'

import { useActionState } from 'react'
import Link from 'next/link'
import { createRequest } from '@/app/requests/actions'


export default function RequestsNewClient() {
  const [error, formAction, isPending] = useActionState(
    async (_prev: unknown, formData: FormData) => {
      try { await createRequest(formData); return null }
      catch (e) { return (e as Error).message }
    },
    null,
  )

  return (
    <main className="container mx-auto p-6 max-w-xl">
      <div className="flex items-center gap-3 mb-6">
        <Link href="/requests" className="text-muted-foreground hover:text-foreground">←</Link>
        <h1 className="text-2xl font-bold text-foreground">Créer Demande</h1>
      </div>

      {error && <p className="mb-4 text-sm text-red-600 bg-red-50 px-4 py-2 rounded">{error}</p>}

      <form action={formAction} className="space-y-4 bg-card rounded-lg border-2 border-border p-6">
        <div>
          <label htmlFor="title" className="block text-sm font-medium text-foreground mb-1">
            Titre <span className="text-red-500">*</span>          </label>
          <input
            type="text"
            id="title"
            name="title"
required             className="w-full px-3 py-2 border border-border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary"
          />
        </div>
        <div>
          <label htmlFor="description" className="block text-sm font-medium text-foreground mb-1">
            Description <span className="text-red-500">*</span>          </label>
          <textarea
            id="description"
            name="description"
            rows={4}
required            className="w-full px-3 py-2 border border-border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary"
          />
        </div>
        <div>
          <label htmlFor="priority" className="block text-sm font-medium text-foreground mb-1">
            Priorité <span className="text-red-500">*</span>          </label>
          <select
            id="priority"
            name="priority"
required            className="w-full px-3 py-2 border border-border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary"
          >
            <option value="">Sélectionner…</option>
            <option value="low">Basse</option>
            <option value="normal">Normale</option>
            <option value="high">Haute</option>
          </select>
        </div>



        <div className="flex gap-3 pt-2">
          <button
            type="submit"
            disabled={isPending}
            className="flex-1 px-6 py-2 bg-primary text-white rounded-md text-sm font-medium hover:bg-primary/85 disabled:opacity-50"
          >
            {isPending ? 'En cours…' : 'Créer'}
          </button>
          <Link
            href="/requests"
            className="px-6 py-2 border border-border rounded-md text-sm font-medium text-foreground hover:bg-muted/50"
          >
            Annuler
          </Link>
        </div>
      </form>
    </main>
  )
}
