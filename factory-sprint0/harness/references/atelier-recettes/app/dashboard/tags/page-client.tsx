'use client'

import { useState } from 'react'
import Link from 'next/link'
import type { SerializedTag } from '@/lib/types'
import { formatDate } from '@/lib/utils'
import { deleteTag } from '@/app/dashboard/tags/actions'

interface DashboardTagsClientProps {
  items: SerializedTag[]
}

export default function DashboardTagsClient({ items }: DashboardTagsClientProps) {
  const [list, setList] = useState(items)
  const [query, setQuery] = useState('')
  const filtered = query
    ? list.filter(item =>
        ['name']
          .some(k => String((item as Record<string, unknown>)[k] ?? '').toLowerCase().includes(query.toLowerCase()))
      )
    : list

  const handleDelete = async (id: string) => {
    if (!confirm('Supprimer cet élément ?')) return
    const result = await deleteTag(id)
    if (result?.error) { alert(result.error); return }
    setList(prev => prev.filter(item => item.id !== id))
  }

  return (
    <main className="container mx-auto p-8">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-foreground">Tags</h1>
        <Link
          href="/dashboard/tags/new"
          className="px-4 py-2 bg-primary text-white rounded-md hover:bg-primary/85 text-sm font-medium"
        >
          Nouveau
        </Link>
      </div>

      <div className="mb-4">
        <input
          type="search"
          placeholder="Rechercher…"
          value={query}
          onChange={e => setQuery(e.target.value)}
          className="w-full max-w-sm px-3 py-2 border border-border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary"
        />
      </div>

      {filtered.length === 0 ? (
        <div className="text-center py-12 text-muted-foreground">
          <p className="text-lg">{query ? 'Aucun résultat pour cette recherche.' : "Aucun élément pour le moment."}</p>
          <Link href="/dashboard/tags/new" className="mt-4 inline-block text-primary hover:underline text-sm">
            Créer le premier
          </Link>
        </div>
      ) : (
        <div className="overflow-hidden bg-card rounded-lg shadow-sm border border-border">
          <table className="min-w-full divide-y divide-border">
            <thead className="bg-muted">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                  Nom
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-muted-foreground uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-card divide-y divide-border">
              {filtered.map(item => (
                <tr key={item.id} className="hover:bg-muted/50 transition-all duration-300 ease-out">
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-foreground">
                    {String(item.name ?? '')}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <div className="flex justify-end gap-2">
                      <Link
                        href={`/dashboard/tags/${item.id}/edit`}
                        className="px-3 py-1 text-xs font-medium text-primary border border-primary rounded hover:bg-primary/10"
                      >
                        Modifier
                      </Link>
                      <button
                        onClick={() => handleDelete(item.id)}
                        className="px-3 py-1 text-xs font-medium text-red-600 border border-red-600 rounded hover:bg-red-50"
                      >
                        Supprimer
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </main>
  )
}
