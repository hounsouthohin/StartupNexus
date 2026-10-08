'use client'

import { useState } from 'react'
import Link from 'next/link'
import type { SerializedForumPost } from '@/lib/types'
import { deleteForumPost } from '@/app/forum-posts/actions'
import { formatDate } from '@/lib/utils'

interface ForumPostsClientProps {
  items: SerializedForumPost[]
}

export default function ForumPostsClient({ items }: ForumPostsClientProps) {
  const [list, setList] = useState(items)

  const handleDelete = async (id: string) => {
    if (!confirm('Supprimer cet élément ?')) return
    const result = await deleteForumPost(id)
    if (result?.error) { alert(result.error); return }
    setList(prev => prev.filter(item => item.id !== id))
  }

  return (
    <main className="container mx-auto p-6">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-foreground">Messages du forum</h1>
        <Link
          href="/forum-posts/new"
          className="px-4 py-2 bg-primary text-white rounded-md hover:bg-primary/85 text-sm font-medium"
        >
          Nouveau
        </Link>
      </div>

      {list.length === 0 ? (
        <div className="text-center py-12 text-muted-foreground">
          <p className="text-lg">Aucun post sur le forum. Créez un nouveau post.</p>
          <Link href="/forum-posts/new" className="mt-4 inline-block text-primary hover:underline text-sm">
            Créer le premier
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {list.map(item => (
            <div
              key={item.id}
              className="bg-card rounded-lg shadow-sm border border-border overflow-hidden transition-all duration-300 ease-out hover:shadow-md group flex flex-col"
            >
              <div className="p-5 flex-1">
                <h2 className="text-base font-semibold text-foreground group-hover:text-primary transition-all duration-300 ease-out mb-2 line-clamp-2">
                  {String(item.title ?? '—')}
                </h2>
                <p className="text-sm text-muted-foreground mb-1 line-clamp-2">
                  <span className="font-medium">Contenu :</span>{' '}
{String(item.content ?? '—')}                </p>
              </div>
              <div className="px-5 py-3 border-t border-border flex items-center justify-end gap-2">
                <Link
                  href={`/forum-posts/${item.id}`}
                  className="px-3 py-1 text-xs font-medium text-muted-foreground border border-border rounded hover:bg-muted/50 transition-all duration-300 ease-out"
                >
                  Voir
                </Link>
                <Link
                  href={`/forum-posts/${item.id}/edit`}
                  className="px-3 py-1 text-xs font-medium text-primary border border-primary rounded hover:bg-primary/10 transition-all duration-300 ease-out"
                >
                  Modifier
                </Link>
                <button
                  onClick={() => handleDelete(item.id)}
                  className="px-3 py-1 text-xs font-medium text-red-600 border border-red-600 rounded hover:bg-red-50 transition-all duration-300 ease-out"
                >
                  Supprimer
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </main>
  )
}
