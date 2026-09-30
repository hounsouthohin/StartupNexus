'use client'

import Link from 'next/link'
import type { SerializedExpenseReport } from '@/lib/types'
import { formatDate } from '@/lib/utils'
import { formatCurrency } from '@/lib/utils'
import { deleteExpenseReport } from '@/app/expense-reports/actions'
import { transitionExpenseReport } from '@/app/expense-reports/actions'

const FIELD_VALUE_LABELS: Record<string, Record<string, string>> = {"category": {"transport": "Transport", "repas": "Repas", "hébergement": "Hébergement", "matériel": "Matériel"}, "status": {"draft": "Brouillon", "submitted": "Soumise", "approved": "Approuvée", "refused": "Refusée", "reimbursed": "Remboursée"}};
// Machine à états (type I) : transitions permises + champs captés à la transition.
const FLOW_TRANSITIONS: Record<string, string[]> = {"approved": ["reimbursed"], "draft": ["submitted"], "refused": [], "reimbursed": [], "submitted": ["approved", "refused"]}
const FLOW_LABELS: Record<string, string> = {"approved": "Approuvée", "draft": "Brouillon", "refused": "Refusée", "reimbursed": "Remboursée", "submitted": "Soumise"}
const FLOW_STATE_FIELDS: Record<string, string[]> = {"refused": ["rejectionReason"]}
const FLOW_FIELD_LABELS: Record<string, string> = {"rejectionReason": "Motif de refus"}

interface ExpenseReportsIdClientProps {
  item: SerializedExpenseReport
}

export default function ExpenseReportsIdClient({ item }: ExpenseReportsIdClientProps) {
  const handleDelete = async () => {
    if (!confirm('Supprimer cet élément ?')) return
    await deleteExpenseReport(item.id)
  }

  return (
    <main className="container mx-auto p-4 max-w-2xl">
      <div className="flex items-center gap-3 mb-6">
        <Link href="/expense-reports" className="text-muted-foreground hover:text-foreground">←</Link>
        <h1 className="text-2xl font-bold text-foreground">Note de frais</h1>
      </div>


      <div className="bg-muted/30 rounded-lg overflow-hidden">
        <dl className="divide-y divide-border">
          <div className="px-6 py-4 grid grid-cols-3 gap-4">
            <dt className="text-sm font-medium text-muted-foreground">Intitulé</dt>
            <dd className="text-sm text-foreground col-span-2">
              {String(item.title ?? '—')}
            </dd>
          </div>
          <div className="px-6 py-4 grid grid-cols-3 gap-4">
            <dt className="text-sm font-medium text-muted-foreground">Montant</dt>
            <dd className="text-sm text-foreground col-span-2">
              {formatCurrency(item.amount)}
            </dd>
          </div>
          <div className="px-6 py-4 grid grid-cols-3 gap-4">
            <dt className="text-sm font-medium text-muted-foreground">Date de dépense</dt>
            <dd className="text-sm text-foreground col-span-2">
              {formatDate(item.expenseDate)}
            </dd>
          </div>
          <div className="px-6 py-4 grid grid-cols-3 gap-4">
            <dt className="text-sm font-medium text-muted-foreground">Catégorie</dt>
            <dd className="text-sm text-foreground col-span-2">
              {(FIELD_VALUE_LABELS['category'] ?? {})[String(item.category)] ?? String(item.category ?? '—')}
            </dd>
          </div>
          <div className="px-6 py-4 grid grid-cols-3 gap-4">
            <dt className="text-sm font-medium text-muted-foreground">Description</dt>
            <dd className="text-sm text-foreground col-span-2">
              {String(item.description ?? '—')}
            </dd>
          </div>
          <div className="px-6 py-4 grid grid-cols-3 gap-4">
            <dt className="text-sm font-medium text-muted-foreground">État</dt>
            <dd className="text-sm text-foreground col-span-2">
              {(FIELD_VALUE_LABELS['status'] ?? {})[String(item.status)] ?? String(item.status ?? '—')}
            </dd>
          </div>
          <div className="px-6 py-4 grid grid-cols-3 gap-4">
            <dt className="text-sm font-medium text-muted-foreground">Motif de refus</dt>
            <dd className="text-sm text-foreground col-span-2">
              {String(item.rejectionReason ?? '—')}
            </dd>
          </div>
        </dl>
      </div>

      {(FLOW_TRANSITIONS[item.status] ?? []).length > 0 && (
        <div className="mt-6 bg-muted/30 rounded-lg p-6">
          <p className="text-sm font-medium text-foreground mb-3">Faire évoluer l&apos;état</p>
          <div className="space-y-3">
            {(FLOW_TRANSITIONS[item.status] ?? []).map(_target => (
              <form key={_target} action={transitionExpenseReport.bind(null, item.id, _target)} className="flex items-end gap-3">
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
          href={`/expense-reports/${item.id}/edit`}
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
          href="/expense-reports"
          className="px-4 py-2 border border-border rounded-md text-sm font-medium text-foreground hover:bg-muted/50"
        >
          Retour
        </Link>
      </div>
    </main>
  )
}
