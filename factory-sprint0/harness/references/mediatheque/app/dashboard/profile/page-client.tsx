'use client'

import Link from 'next/link'
import type { SerializedMember } from '@/lib/types'
import { formatDate } from '@/lib/utils'
import { deleteMember } from '@/app/members/actions'

interface DashboardProfileClientProps {
  item: SerializedMember
}

export default function DashboardProfileClient({ item }: DashboardProfileClientProps) {
  const handleDelete = async () => {
    if (!confirm('Supprimer cet élément ?')) return
    await deleteMember(item.id)
  }

  return (
    <main className="container mx-auto p-8 max-w-2xl">
      <div className="flex items-center gap-3 mb-6">
        <Link href="/members" className="text-muted-foreground hover:text-foreground">←</Link>
        <h1 className="text-2xl font-bold text-foreground">Adhérent</h1>
      </div>


      <div className="bg-muted/30 rounded-lg overflow-hidden">
        <dl className="divide-y divide-border">
          <div className="px-6 py-4 grid grid-cols-3 gap-4">
            <dt className="text-sm font-medium text-muted-foreground">Nom</dt>
            <dd className="text-sm text-foreground col-span-2">
              {String(item.name ?? '—')}
            </dd>
          </div>
          <div className="px-6 py-4 grid grid-cols-3 gap-4">
            <dt className="text-sm font-medium text-muted-foreground">Email</dt>
            <dd className="text-sm text-foreground col-span-2">
              {String(item.email ?? '—')}
            </dd>
          </div>
          <div className="px-6 py-4 grid grid-cols-3 gap-4">
            <dt className="text-sm font-medium text-muted-foreground">Téléphone</dt>
            <dd className="text-sm text-foreground col-span-2">
              {String(item.phone ?? '—')}
            </dd>
          </div>
        </dl>
      </div>


      <div className="mt-6 flex gap-3">
        <Link
          href={`/members/${item.id}/edit`}
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
          href="/members"
          className="px-4 py-2 border border-border rounded-md text-sm font-medium text-foreground hover:bg-muted/50"
        >
          Retour
        </Link>
      </div>
    </main>
  )
}
