'use client'

import { useState } from 'react'
import Link from 'next/link'
import type { SerializedRequest } from '@/lib/types'
import { deleteRequest } from '@/app/requests/actions'
import { formatDate } from '@/lib/utils'

const STATUS_COLORS: Record<string, string> = {
  new: 'bg-muted text-muted-foreground',
  in_progress: 'bg-blue-100  text-blue-800',
  resolved: 'bg-muted text-muted-foreground',
}

const STATUS_LABELS: Record<string, string> = {
  'new': 'Nouvelle',
  'in_progress': 'En cours',
  'resolved': 'Résolue',
}
const FIELD_ENUM_LABELS: Record<string, Record<string, string>> = {
  priority: { 'low': 'Basse', 'normal': 'Normale', 'high': 'Haute', },
}

const statusColor = (s: string) =>
  STATUS_COLORS[s?.toLowerCase()] ?? 'bg-muted text-muted-foreground'

interface RequestsClientProps {
  items: SerializedRequest[]
}

export default function RequestsClient({ items }: RequestsClientProps) {
  const [list, setList] = useState(items)
  const [statusFilter, setStatusFilter] = useState('')

  const filtered = list
    .filter(item => !statusFilter || (item as Record<string, unknown>).status === statusFilter)

  const handleDelete = async (id: string) => {
    if (!confirm('Supprimer cet élément ?')) return
    const result = await deleteRequest(id)
    if (result?.error) { alert(result.error); return }
    setList(prev => prev.filter(item => item.id !== id))
  }

  return (
    <main className="container mx-auto p-6">
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-2xl font-bold text-foreground">Demandes</h1>
        <Link href="/requests/new" className="px-4 py-2 bg-primary text-white rounded-md hover:bg-primary/85 text-sm font-medium">
          Nouveau
        </Link>
      </div>

      <div className="flex flex-wrap gap-3 mb-4">
        <select
          value={statusFilter}
          onChange={e => setStatusFilter(e.target.value)}
          className="px-3 py-2 border border-border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary"
        >
          <option value="">Tous les statuts</option>
          <option value="new">Nouvelle</option>
          <option value="in_progress">En cours</option>
          <option value="resolved">Résolue</option>
        </select>
      </div>

      {filtered.length === 0 ? (
        <div className="text-center py-12 text-muted-foreground">
          <p>{list.length === 0 ? "Aucune demande. Créez votre première demande." : 'Aucun résultat pour ce filtre.'}</p>
        </div>
      ) : (
        <div className="overflow-hidden bg-card rounded-lg border-2 border-border">
          <table className="min-w-full divide-y divide-border">
            <thead className="bg-muted">
              <tr>
<th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">Titre</th>
<th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">Description</th>
<th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">Priorité</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">Statut</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-muted-foreground uppercase tracking-wider">Actions</th>
              </tr>
            </thead>
            <tbody className="bg-card divide-y divide-border">
              {filtered.map(item => (
                <tr key={item.id} className="hover:bg-muted/50 transition-colors duration-150">
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-foreground">{String(item.title ?? '')}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-foreground">{String(item.description ?? '')}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-foreground">{FIELD_ENUM_LABELS.priority?.[String(item.priority ?? '')] ?? String(item.priority ?? '')}</td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${statusColor(String((item as Record<string, unknown>).status ?? ''))}`}>
                      {STATUS_LABELS[String((item as Record<string, unknown>).status ?? '')] ?? String((item as Record<string, unknown>).status ?? '—')}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <div className="flex justify-end gap-2">
                      <Link href={`/requests/${item.id}/edit`} className="px-3 py-1 text-xs font-medium text-primary border border-primary rounded hover:bg-primary/10">
                        Modifier
                      </Link>
                      <button onClick={() => handleDelete(item.id)} className="px-3 py-1 text-xs font-medium text-red-600 border border-red-600 rounded hover:bg-red-50">
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
