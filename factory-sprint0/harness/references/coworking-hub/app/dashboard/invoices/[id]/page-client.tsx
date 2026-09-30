'use client'

import Link from 'next/link'
import type { SerializedInvoice } from '@/lib/types'
import { formatDate } from '@/lib/utils'
import { formatCurrency } from '@/lib/utils'
import { deleteInvoice } from '@/app/dashboard/invoices/actions'
import { transitionInvoice } from '@/app/dashboard/invoices/actions'

const FIELD_VALUE_LABELS: Record<string, Record<string, string>> = {"status": {"pending": "En attente de paiement", "paid": "Payée", "overdue": "En retard"}};
// Machine à états (type I) : transitions permises + champs captés à la transition.
const FLOW_TRANSITIONS: Record<string, string[]> = {"overdue": [], "paid": [], "pending": ["paid", "overdue"]}
const FLOW_LABELS: Record<string, string> = {"overdue": "En retard", "paid": "Payée", "pending": "En attente de paiement"}
const FLOW_STATE_FIELDS: Record<string, string[]> = {}
const FLOW_FIELD_LABELS: Record<string, string> = {}

interface DashboardInvoicesIdClientProps {
  item: SerializedInvoice
}

export default function DashboardInvoicesIdClient({ item }: DashboardInvoicesIdClientProps) {
  const handleDelete = async () => {
    if (!confirm('Supprimer cet élément ?')) return
    await deleteInvoice(item.id)
  }

  return (
    <main className="container mx-auto p-4 max-w-2xl">
      <div className="flex items-center gap-3 mb-6">
        <Link href="/dashboard/invoices" className="text-muted-foreground hover:text-foreground">←</Link>
        <h1 className="text-2xl font-bold text-foreground">Facture</h1>
      </div>


      <div className="bg-muted/30 rounded-lg overflow-hidden">
        <dl className="divide-y divide-border">
          <div className="px-6 py-4 grid grid-cols-3 gap-4">
            <dt className="text-sm font-medium text-muted-foreground">Montant</dt>
            <dd className="text-sm text-foreground col-span-2">
              {formatCurrency(item.amount)}
            </dd>
          </div>
          <div className="px-6 py-4 grid grid-cols-3 gap-4">
            <dt className="text-sm font-medium text-muted-foreground">Date d'émission</dt>
            <dd className="text-sm text-foreground col-span-2">
              {formatDate(item.issueDate)}
            </dd>
          </div>
          <div className="px-6 py-4 grid grid-cols-3 gap-4">
            <dt className="text-sm font-medium text-muted-foreground">Statut</dt>
            <dd className="text-sm text-foreground col-span-2">
              {(FIELD_VALUE_LABELS['status'] ?? {})[String(item.status)] ?? String(item.status ?? '—')}
            </dd>
          </div>
        </dl>
      </div>

      {(FLOW_TRANSITIONS[item.status] ?? []).length > 0 && (
        <div className="mt-6 bg-muted/30 rounded-lg p-6">
          <p className="text-sm font-medium text-foreground mb-3">Faire évoluer l&apos;état</p>
          <div className="space-y-3">
            {(FLOW_TRANSITIONS[item.status] ?? []).map(_target => (
              <form key={_target} action={transitionInvoice.bind(null, item.id, _target)} className="flex items-end gap-3">
                {(FLOW_STATE_FIELDS[_target] ?? []).map(_f => (
                  <div key={_f} className="flex-1">
                    <label htmlFor={_f} className="block text-xs font-medium text-muted-foreground mb-1">{FLOW_FIELD_LABELS[_f] ?? _f}</label>
                    <textarea id={_f} name={_f} required rows={2} className="w-full px-3 py-2 border border-border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary" />
                  </div>
                ))}
                <button type="submit" className="px-4 py-2 bg-primary text-white rounded-md hover:bg-primary/85 text-sm font-medium whitespace-nowrap">
                  {FLOW_LABELS[_target] ?? _target}
                </button>
              </form>
            ))}
          </div>
        </div>
      )}

      <div className="mt-6 flex gap-3">
        <Link
          href={`/dashboard/invoices/${item.id}/edit`}
          className="px-4 py-2 bg-primary text-white rounded-md hover:bg-primary/85 text-sm font-medium"
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
          href="/dashboard/invoices"
          className="px-4 py-2 border border-border rounded-md text-sm font-medium text-foreground hover:bg-muted/50"
        >
          Retour
        </Link>
      </div>
    </main>
  )
}
