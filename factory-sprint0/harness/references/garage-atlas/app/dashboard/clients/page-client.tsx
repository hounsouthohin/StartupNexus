'use client'

import { useState } from 'react'
import Link from 'next/link'
import type { SerializedClient } from '@/lib/types'
import { formatDate } from '@/lib/utils'
import { deleteClient } from '@/app/dashboard/clients/actions'

interface DashboardClientsClientProps {
  items: SerializedClient[]
}

export default function DashboardClientsClient({ items }: DashboardClientsClientProps) {
  const [list, setList] = useState(items)
  const filtered = list

  const handleDelete = async (id: string) => {
    if (!confirm('Supprimer cet élément ?')) return
    const result = await deleteClient(id)
    if (result?.error) { alert(result.error); return }
    setList(prev => prev.filter(item => item.id !== id))
  }

  return (
    <main className="container mx-auto p-4">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-foreground">Clients</h1>
        <Link
          href="/dashboard/clients/new"
          className="px-4 py-2 bg-primary text-white rounded-md hover:bg-primary/85 text-sm font-medium"
        >
          Nouveau
        </Link>
      </div>

      {filtered.length === 0 ? (
        <div className="text-center py-12 text-muted-foreground">
          <p className="text-lg">Aucun élément pour le moment.</p>
          <Link href="/dashboard/clients/new" className="mt-4 inline-block text-primary hover:underline text-sm">
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
                <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                  Téléphone
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-muted-foreground uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-card divide-y divide-border">
              {filtered.map(item => (
                <tr key={item.id} className="hover:bg-muted/50 transition-colors duration-150">
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-foreground">
                    {String(item.name ?? '')}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-foreground">
                    {String(item.phone ?? '')}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <div className="flex justify-end gap-2">
                      <Link
                        href={`/dashboard/clients/${item.id}`}
                        className="px-3 py-1 text-xs font-medium text-muted-foreground border border-border rounded hover:bg-muted/50"
                      >
                        Voir
                      </Link>
                      <Link
                        href={`/dashboard/clients/${item.id}/edit`}
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
