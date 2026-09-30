'use client'

import { useState } from 'react'
import Link from 'next/link'
import type { SerializedReservation } from '@/lib/types'
import { deleteReservation } from '@/app/dashboard/reservations/actions'
import { formatDate } from '@/lib/utils'

const STATUS_COLORS: Record<string, string> = {
  requested: 'bg-muted text-muted-foreground',
  confirmed: 'bg-muted text-muted-foreground',
  refused: 'bg-muted text-muted-foreground',
  completed: 'bg-green-100 text-green-800',
  cancelled: 'bg-red-100   text-red-800',
}

const STATUS_LABELS: Record<string, string> = {
  'requested': 'Demandée',
  'confirmed': 'Confirmée',
  'refused': 'Refusée',
  'completed': 'Terminée',
  'cancelled': 'Annulée',
}

const statusColor = (s: string) =>
  STATUS_COLORS[s?.toLowerCase()] ?? 'bg-muted text-muted-foreground'

interface DashboardReservationsClientProps {
  items: SerializedReservation[]
}

export default function DashboardReservationsClient({ items }: DashboardReservationsClientProps) {
  const [list, setList] = useState(items)
  const [statusFilter, setStatusFilter] = useState('')

  const filtered = list
    .filter(item => !statusFilter || (item as Record<string, unknown>).status === statusFilter)

  const handleDelete = async (id: string) => {
    if (!confirm('Supprimer cet élément ?')) return
    const result = await deleteReservation(id)
    if (result?.error) { alert(result.error); return }
    setList(prev => prev.filter(item => item.id !== id))
  }

  return (
    <main className="container mx-auto p-4">
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-2xl font-bold text-foreground">Réservations</h1>
        <Link href="/dashboard/reservations/new" className="px-4 py-2 bg-primary text-white rounded-md hover:bg-primary/85 text-sm font-medium">
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
          <option value="requested">Demandée</option>
          <option value="confirmed">Confirmée</option>
          <option value="refused">Refusée</option>
          <option value="completed">Terminée</option>
          <option value="cancelled">Annulée</option>
        </select>
      </div>

      {filtered.length === 0 ? (
        <div className="text-center py-12 text-muted-foreground">
          <p>{list.length === 0 ? "Aucun élément pour le moment." : 'Aucun résultat pour ce filtre.'}</p>
        </div>
      ) : (
        <div className="overflow-hidden bg-muted/30 rounded-lg">
          <table className="min-w-full divide-y divide-border">
            <thead className="bg-muted">
              <tr>
<th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">Date</th>
<th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">Heure de début</th>
<th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">Heure de fin</th>
<th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">Space</th>
<th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">Member</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">Statut</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-muted-foreground uppercase tracking-wider">Actions</th>
              </tr>
            </thead>
            <tbody className="bg-card divide-y divide-border">
              {filtered.map(item => (
                <tr key={item.id} className="hover:bg-muted/50 transition-none">
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-foreground">{formatDate(item.date)}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-foreground">{formatDate(item.startTime)}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-foreground">{formatDate(item.endTime)}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-muted-foreground">{String((item as any).space?.name ?? '—')}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-muted-foreground">{String((item as any).member?.name ?? '—')}</td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${statusColor(String((item as Record<string, unknown>).status ?? ''))}`}>
                      {STATUS_LABELS[String((item as Record<string, unknown>).status ?? '')] ?? String((item as Record<string, unknown>).status ?? '—')}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <div className="flex justify-end gap-2">
                      <Link href={`/dashboard/reservations/${item.id}/edit`} className="px-3 py-1 text-xs font-medium text-primary border border-primary rounded hover:bg-primary/10">
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
