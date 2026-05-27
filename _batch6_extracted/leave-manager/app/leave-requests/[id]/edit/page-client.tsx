'use client'

import { useActionState } from 'react'
import Link from 'next/link'
import type { SerializedLeaveRequest } from '@/lib/types'
import { updateLeaveRequest } from '@/app/leave-requests/actions'

interface LeaveRequestEditClientProps {
  item: SerializedLeaveRequest
}

export default function LeaveRequestEditClient({ item }: LeaveRequestEditClientProps) {
  const [error, formAction, isPending] = useActionState(
    async (_prev: unknown, formData: FormData) => {
      try { await updateLeaveRequest.bind(null, item.id)(formData); return null }
      catch (e) { return (e as Error).message }
    },
    null,
  )

  return (
    <main className="container mx-auto p-6 max-w-xl">
      <div className="flex items-center gap-3 mb-6">
        <Link href="/leave-requests" className="text-gray-400 hover:text-gray-600">←</Link>
        <h1 className="text-2xl font-bold text-gray-900">Modifier LeaveRequest</h1>
      </div>

      {error && <p className="mb-4 text-sm text-red-600 bg-red-50 px-4 py-2 rounded">{error}</p>}

      <form action={updateLeaveRequest.bind(null, item.id)} className="space-y-4 bg-white p-6 rounded-lg shadow-sm border border-gray-200">
        <div>
          <label htmlFor="startDate" className="block text-sm font-medium text-gray-700 mb-1">
            startDate
          </label>
          <input
            type="date"
            id="startDate"
            name="startDate"
            defaultValue={item.startDate != null ? String(item.startDate) : ''}
            className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <div>
          <label htmlFor="endDate" className="block text-sm font-medium text-gray-700 mb-1">
            endDate
          </label>
          <input
            type="date"
            id="endDate"
            name="endDate"
            defaultValue={item.endDate != null ? String(item.endDate) : ''}
            className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <div>
          <label htmlFor="reason" className="block text-sm font-medium text-gray-700 mb-1">
            reason
          </label>
          <textarea
            id="reason"
            name="reason"
            rows={4}
            defaultValue={item.reason ?? ''}
            className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <div>
          <label htmlFor="type" className="block text-sm font-medium text-gray-700 mb-1">
            type
          </label>
          <select
            id="type"
            name="type"
            defaultValue={item.type ?? ''}
            className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">Sélectionner…</option>
            <option value="annual_leave">annual_leave</option>
            <option value="sick_leave">sick_leave</option>
            <option value="unpaid_leave">unpaid_leave</option>
          </select>
        </div>
        <div>
          <label htmlFor="status" className="block text-sm font-medium text-gray-700 mb-1">
            status
          </label>
          <select
            id="status"
            name="status"
            defaultValue={item.status ?? ''}
            className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">Sélectionner…</option>
            <option value="pending">pending</option>
            <option value="approved">approved</option>
            <option value="rejected">rejected</option>
          </select>
        </div>


        <div className="flex gap-3 pt-2">
          <button
            type="submit"
            disabled={isPending}
            className="flex-1 px-6 py-2 bg-blue-600 text-white rounded-md text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
          >
            {isPending ? 'En cours…' : 'Enregistrer'}
          </button>
          <Link
            href="/leave-requests"
            className="px-6 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50"
          >
            Annuler
          </Link>
        </div>
      </form>
    </main>
  )
}
