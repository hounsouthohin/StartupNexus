'use client'

import { useActionState } from 'react'
import Link from 'next/link'
import type { SerializedExpenseReport } from '@/lib/types'
import { updateExpenseReport } from '@/app/expense-reports/actions'

// Verrou d'édition (type I) : dans ces états les champs métier sont figés. Le changement
// d'état lui-même se fait via les boutons de transition de la page détail, pas ici.
const FLOW_LOCKED: string[] = ["approved", "refused", "reimbursed", "submitted"]

interface ExpenseReportEditClientProps {
  item: SerializedExpenseReport
}

export default function ExpenseReportEditClient({ item }: ExpenseReportEditClientProps) {
  const [error, formAction, isPending] = useActionState(
    async (_prev: unknown, formData: FormData) => {
      try { await updateExpenseReport.bind(null, item.id)(formData); return null }
      catch (e) { return (e as Error).message }
    },
    null,
  )
  const _isLocked = FLOW_LOCKED.includes(item.status)

  return (
    <main className="container mx-auto p-4 max-w-xl">
      <div className="flex items-center gap-3 mb-6">
        <Link href="/expense-reports" className="text-muted-foreground hover:text-foreground">←</Link>
        <h1 className="text-2xl font-bold text-foreground">Modifier Note de frais</h1>
      </div>

      {error && <p className="mb-4 text-sm text-red-600 bg-red-50 px-4 py-2 rounded">{error}</p>}
      {_isLocked && (
        <p className="mb-4 text-sm text-amber-800 bg-amber-50 border border-amber-200 px-4 py-2 rounded">
          Les informations ne sont plus modifiables à ce stade. Vous pouvez encore faire évoluer l&apos;état.
        </p>
      )}

      <form action={formAction} className="space-y-4 bg-muted/30 rounded-lg p-4">
        <div>
          <label htmlFor="title" className="block text-sm font-medium text-foreground mb-1">
            Intitulé
          </label>
          <input
            type="text"
            id="title"
            name="title"
            defaultValue={item.title != null ? String(item.title) : ''}
disabled={_isLocked}             className="w-full px-3 py-2 border border-border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary disabled:bg-muted disabled:text-muted-foreground"
          />
        </div>
        <div>
          <label htmlFor="amount" className="block text-sm font-medium text-foreground mb-1">
            Montant
          </label>
          <input
            type="number"
            id="amount"
            name="amount"
            defaultValue={item.amount != null ? String(item.amount) : ''}
step="any" disabled={_isLocked}             className="w-full px-3 py-2 border border-border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary disabled:bg-muted disabled:text-muted-foreground"
          />
        </div>
        <div>
          <label htmlFor="expenseDate" className="block text-sm font-medium text-foreground mb-1">
            Date de dépense
          </label>
          <input
            type="date"
            id="expenseDate"
            name="expenseDate"
            defaultValue={item.expenseDate ? (item.expenseDate as string).slice(0, 10) : ''}
disabled={_isLocked}            className="w-full px-3 py-2 border border-border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary disabled:bg-muted disabled:text-muted-foreground"
          />
        </div>
        <div>
          <label htmlFor="category" className="block text-sm font-medium text-foreground mb-1">
            Catégorie
          </label>
          <select
            id="category"
            name="category"
            defaultValue={item.category ?? ''}
disabled={_isLocked}            className="w-full px-3 py-2 border border-border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary disabled:bg-muted disabled:text-muted-foreground"
          >
            <option value="">Sélectionner…</option>
            <option value="transport">Transport</option>
            <option value="repas">Repas</option>
            <option value="hébergement">Hébergement</option>
            <option value="matériel">Matériel</option>
          </select>
        </div>
        <div>
          <label htmlFor="description" className="block text-sm font-medium text-foreground mb-1">
            Description
          </label>
          <textarea
            id="description"
            name="description"
            rows={4}
            defaultValue={item.description ?? ''}
disabled={_isLocked}            className="w-full px-3 py-2 border border-border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary disabled:bg-muted disabled:text-muted-foreground"
          />
        </div>



        <div className="flex gap-3 pt-2">
          <button
            type="submit"
            disabled={isPending}
            className="flex-1 px-6 py-2 bg-primary text-white rounded-md text-sm font-medium hover:bg-primary/85 disabled:opacity-50"
          >
            {isPending ? 'En cours…' : 'Enregistrer'}
          </button>
          <Link
            href="/expense-reports"
            className="px-6 py-2 border border-border rounded-md text-sm font-medium text-foreground hover:bg-muted/50"
          >
            Annuler
          </Link>
        </div>
      </form>
    </main>
  )
}
