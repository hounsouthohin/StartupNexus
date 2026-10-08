'use client'

import { useActionState } from 'react'
import Link from 'next/link'
import type { SerializedDelay } from '@/lib/types'
import { updateDelay } from '@/app/delays/actions'


interface DelayEditClientProps {
  item: SerializedDelay
}

export default function DelayEditClient({ item }: DelayEditClientProps) {
  const [error, formAction, isPending] = useActionState(
    async (_prev: unknown, formData: FormData) => {
      try { await updateDelay.bind(null, item.id)(formData); return null }
      catch (e) { return (e as Error).message }
    },
    null,
  )

  return (
    <main className="container mx-auto p-6 max-w-xl">
      <div className="flex items-center gap-3 mb-6">
        <Link href="/delays" className="text-muted-foreground hover:text-foreground">←</Link>
        <h1 className="text-2xl font-bold text-foreground">Modifier Retard</h1>
      </div>

      {error && <p className="mb-4 text-sm text-red-600 bg-red-50 px-4 py-2 rounded">{error}</p>}

      <form action={formAction} className="space-y-4 bg-card rounded-lg shadow-sm border border-border p-6">
        <div>
          <label htmlFor="date" className="block text-sm font-medium text-foreground mb-1">
            Date
          </label>
          <input
            type="datetime-local"
            id="date"
            name="date"
            defaultValue={item.date ? new Date(item.date as string).toISOString().slice(0, 16) : ''}
            className="w-full px-3 py-2 border border-border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary disabled:bg-muted disabled:text-muted-foreground"
          />
        </div>
        <div>
          <label htmlFor="reason" className="block text-sm font-medium text-foreground mb-1">
            Raison
          </label>
          <input
            type="text"
            id="reason"
            name="reason"
            defaultValue={item.reason != null ? String(item.reason) : ''}
            className="w-full px-3 py-2 border border-border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary disabled:bg-muted disabled:text-muted-foreground"
          />
        </div>
        <div>
          <label htmlFor="studentId" className="block text-sm font-medium text-foreground mb-1">
            studentId
          </label>
          <input
            type="text"
            id="studentId"
            name="studentId"
            defaultValue={item.studentId != null ? String(item.studentId) : ''}
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
            href="/delays"
            className="px-6 py-2 border border-border rounded-md text-sm font-medium text-foreground hover:bg-muted/50"
          >
            Annuler
          </Link>
        </div>
      </form>
    </main>
  )
}
