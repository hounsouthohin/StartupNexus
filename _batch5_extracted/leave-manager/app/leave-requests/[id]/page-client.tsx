'use client'

import Link from 'next/link'
import type { SerializedLeaveRequest } from '@/lib/types'
import { deleteLeaveRequest } from '@/app/leave-requests/actions'

interface LeaveRequestsIdClientProps {
  item: SerializedLeaveRequest
}

export default function LeaveRequestsIdClient({ item }: LeaveRequestsIdClientProps) {
  const handleDelete = async () => {
    if (!confirm('Supprimer cet élément ?')) return
    await deleteLeaveRequest(item.id)
  }

  return (
    <main className="container mx-auto p-6 max-w-2xl">
      <div className="flex items-center gap-3 mb-6">
        <Link href="/leave-requests" className="text-gray-400 hover:text-gray-600">←</Link>
        <h1 className="text-2xl font-bold text-gray-900">LeaveRequest</h1>
      </div>

      <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
        <dl className="divide-y divide-gray-100">
          <div className="px-6 py-4 grid grid-cols-3 gap-4">
            <dt className="text-sm font-medium text-gray-500">startDate</dt>
            <dd className="text-sm text-gray-900 col-span-2">{String(item.startDate ?? '—')}</dd>
          </div>
          <div className="px-6 py-4 grid grid-cols-3 gap-4">
            <dt className="text-sm font-medium text-gray-500">endDate</dt>
            <dd className="text-sm text-gray-900 col-span-2">{String(item.endDate ?? '—')}</dd>
          </div>
          <div className="px-6 py-4 grid grid-cols-3 gap-4">
            <dt className="text-sm font-medium text-gray-500">reason</dt>
            <dd className="text-sm text-gray-900 col-span-2">{String(item.reason ?? '—')}</dd>
          </div>
          <div className="px-6 py-4 grid grid-cols-3 gap-4">
            <dt className="text-sm font-medium text-gray-500">type</dt>
            <dd className="text-sm text-gray-900 col-span-2">{String(item.type ?? '—')}</dd>
          </div>
          <div className="px-6 py-4 grid grid-cols-3 gap-4">
            <dt className="text-sm font-medium text-gray-500">status</dt>
            <dd className="text-sm text-gray-900 col-span-2">{String(item.status ?? '—')}</dd>
          </div>
        </dl>
      </div>

      <div className="mt-6 flex gap-3">
        <Link
          href={`/leave-requests/${item.id}/edit`}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 text-sm font-medium"
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
          href="/leave-requests"
          className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50"
        >
          Retour
        </Link>
      </div>
    </main>
  )
}
