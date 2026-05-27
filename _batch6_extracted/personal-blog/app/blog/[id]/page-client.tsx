'use client'

import Link from 'next/link'
import type { SerializedPost } from '@/lib/types'

interface BlogIdClientProps {
  item: SerializedPost
}

export default function BlogIdClient({ item }: BlogIdClientProps) {

  return (
    <main className="container mx-auto p-6 max-w-2xl">
      <div className="flex items-center gap-3 mb-6">
        <Link href="/blog" className="text-gray-400 hover:text-gray-600">←</Link>
        <h1 className="text-2xl font-bold text-gray-900">Post</h1>
      </div>

      <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
        <dl className="divide-y divide-gray-100">
          <div className="px-6 py-4 grid grid-cols-3 gap-4">
            <dt className="text-sm font-medium text-gray-500">title</dt>
            <dd className="text-sm text-gray-900 col-span-2">{String(item.title ?? '—')}</dd>
          </div>
          <div className="px-6 py-4 grid grid-cols-3 gap-4">
            <dt className="text-sm font-medium text-gray-500">excerpt</dt>
            <dd className="text-sm text-gray-900 col-span-2">{String(item.excerpt ?? '—')}</dd>
          </div>
          <div className="px-6 py-4 grid grid-cols-3 gap-4">
            <dt className="text-sm font-medium text-gray-500">published</dt>
            <dd className="text-sm text-gray-900 col-span-2">{String(item.published ?? '—')}</dd>
          </div>
        </dl>
      </div>

      <div className="mt-6 flex gap-3">
        <Link
          href={`/blog/${item.id}/edit`}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 text-sm font-medium"
        >
          Modifier
        </Link>
        <Link
          href="/blog"
          className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50"
        >
          Retour
        </Link>
      </div>
    </main>
  )
}
