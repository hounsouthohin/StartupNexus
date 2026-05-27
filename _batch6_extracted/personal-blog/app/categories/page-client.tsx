'use client'

import { useState } from 'react'
import Link from 'next/link'
import type { SerializedCategory } from '@/lib/types'
import { deleteCategory } from '@/app/categories/actions'

interface CategoriesClientProps {
  items: SerializedCategory[]
}

export default function CategoriesClient({ items }: CategoriesClientProps) {
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
    await deleteCategory(id)
    setList(prev => prev.filter(item => item.id !== id))
  }

  return (
    <main className="container mx-auto p-6">
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-2xl font-bold text-gray-900">Categorys</h1>
        <Link href="/categories/new" className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 text-sm font-medium">
          Nouveau
        </Link>
      </div>

      <div className="mb-4">
        <input
          type="search"
          placeholder="Rechercher…"
          value={query}
          onChange={e => setQuery(e.target.value)}
          className="w-full max-w-sm px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      {filtered.length === 0 ? (
        <div className="text-center py-12 text-gray-500">
          <p>{query ? 'Aucun résultat pour cette recherche.' : 'Aucun élément.'}</p>
        </div>
      ) : (
        <div className="overflow-hidden shadow ring-1 ring-black ring-opacity-5 rounded-lg">
          <table className="min-w-full divide-y divide-gray-300">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">name</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filtered.map(item => (
                <tr key={item.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{String(item.name ?? '')}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <div className="flex justify-end gap-2">
                      <Link href={`/categories/${item.id}/edit`} className="px-3 py-1 text-xs font-medium text-blue-600 border border-blue-600 rounded hover:bg-blue-50">
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
