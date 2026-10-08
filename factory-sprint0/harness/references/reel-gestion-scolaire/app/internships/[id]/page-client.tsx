'use client'

import Link from 'next/link'
import type { SerializedInternship } from '@/lib/types'
import { formatDate } from '@/lib/utils'
import { deleteInternship } from '@/app/internships/actions'

interface InternshipsIdClientProps {
  item: SerializedInternship
}

export default function InternshipsIdClient({ item }: InternshipsIdClientProps) {
  const handleDelete = async () => {
    if (!confirm('Supprimer cet élément ?')) return
    await deleteInternship(item.id)
  }

  return (
    <main className="container mx-auto p-6 max-w-2xl">
      <div className="flex items-center gap-3 mb-6">
        <Link href="/internships" className="text-muted-foreground hover:text-foreground">←</Link>
        <h1 className="text-2xl font-bold text-foreground">Stage</h1>
      </div>


      <div className="bg-card rounded-lg shadow-sm border border-border overflow-hidden">
        <dl className="divide-y divide-border">
          <div className="px-6 py-4 grid grid-cols-3 gap-4">
            <dt className="text-sm font-medium text-muted-foreground">Nom de l'entreprise</dt>
            <dd className="text-sm text-foreground col-span-2">
              {String(item.companyName ?? '—')}
            </dd>
          </div>
          <div className="px-6 py-4 grid grid-cols-3 gap-4">
            <dt className="text-sm font-medium text-muted-foreground">Durée</dt>
            <dd className="text-sm text-foreground col-span-2">
              {String(item.duration ?? '—')}
            </dd>
          </div>
          <div className="px-6 py-4 grid grid-cols-3 gap-4">
            <dt className="text-sm font-medium text-muted-foreground">studentId</dt>
            <dd className="text-sm text-foreground col-span-2">
              {String(item.studentId ?? '—')}
            </dd>
          </div>
        </dl>
      </div>


      <div className="mt-6 flex gap-3">
        <Link
          href={`/internships/${item.id}/edit`}
          className="px-4 py-2 bg-primary text-white rounded-md hover:bg-primary/85 text-sm font-medium"
        >
          Modifier
        </Link>
        <button
          onClick={handleDelete}
          className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 text-sm font-medium"
        >
          Supprimer
        </button>
        <Link
          href="/internships"
          className="px-4 py-2 border border-border rounded-md text-sm font-medium text-foreground hover:bg-muted/50"
        >
          Retour
        </Link>
      </div>
    </main>
  )
}
