'use client'

import Link from 'next/link'
import type { SerializedSpace } from '@/lib/types'
import { formatDate } from '@/lib/utils'
import { formatCurrency } from '@/lib/utils'

interface SpacesClientProps {
  items: SerializedSpace[]
}

export default function SpacesClient({ items }: SpacesClientProps) {
  return (
    <main className="container mx-auto p-4">
      <h1 className="text-2xl font-bold text-foreground mb-6">Espaces</h1>

      {items.length === 0 ? (
        <div className="text-center py-12 text-muted-foreground">
          <p className="text-lg">Aucun espace disponible pour le moment.</p>
        </div>
      ) : (
        <div className="overflow-hidden bg-muted/30 rounded-lg">
          <table className="min-w-full divide-y divide-border">
            <thead className="bg-muted">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                  Nom
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                  Type
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                  Capacité
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-muted-foreground uppercase tracking-wider">
                  Détail
                </th>
              </tr>
            </thead>
            <tbody className="bg-card divide-y divide-border">
              {items.map(item => (
                <tr key={item.id} className="hover:bg-muted/50 transition-none">
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-foreground">
                    {String(item.name ?? '')}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-foreground">
                    {String(item.type ?? '')}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-foreground">
                    {String(item.capacity ?? '')}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <Link
                      href={`/spaces/${item.id}`}
                      className="px-3 py-1 text-xs font-medium text-primary border border-primary rounded hover:bg-primary/10"
                    >
                      Lire
                    </Link>
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
