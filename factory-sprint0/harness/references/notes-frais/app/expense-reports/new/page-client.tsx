'use client'

import { useActionState } from 'react'
import Link from 'next/link'
import { createExpenseReport } from '@/app/expense-reports/actions'


export default function ExpenseReportsNewClient() {
  const [error, formAction, isPending] = useActionState(
    async (_prev: unknown, formData: FormData) => {
      try { await createExpenseReport(formData); return null }
      catch (e) { return (e as Error).message }
    },
    null,
  )

  return (
    <main className="container mx-auto p-4 max-w-xl">
      <div className="flex items-center gap-3 mb-6">
        <Link href="/expense-reports" className="text-muted-foreground hover:text-foreground">←</Link>
        <h1 className="text-2xl font-bold text-foreground">Créer Note de frais</h1>
      </div>

      {error && <p className="mb-4 text-sm text-red-600 bg-red-50 px-4 py-2 rounded">{error}</p>}

      <form action={formAction} className="space-y-4 bg-muted/30 rounded-lg p-4">
        <div>
          <label htmlFor="title" className="block text-sm font-medium text-foreground mb-1">
            Intitulé <span className="text-red-500">*</span>          </label>
          <input
            type="text"
            id="title"
            name="title"
required             className="w-full px-3 py-2 border border-border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary"
          />
        </div>
        <div>
          <label htmlFor="amount" className="block text-sm font-medium text-foreground mb-1">
            Montant <span className="text-red-500">*</span>          </label>
          <input
            type="number"
            id="amount"
            name="amount"
required step="any"            className="w-full px-3 py-2 border border-border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary"
          />
        </div>
        <div>
          <label htmlFor="expenseDate" className="block text-sm font-medium text-foreground mb-1">
            Date de dépense <span className="text-red-500">*</span>          </label>
          <input
            type="date"
            id="expenseDate"
            name="expenseDate"
required             className="w-full px-3 py-2 border border-border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary"
          />
        </div>
        <div>
          <label htmlFor="category" className="block text-sm font-medium text-foreground mb-1">
            Catégorie <span className="text-red-500">*</span>          </label>
          <select
            id="category"
            name="category"
required            className="w-full px-3 py-2 border border-border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary"
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
            Description          </label>
          <textarea
            id="description"
            name="description"
            rows={4}
            className="w-full px-3 py-2 border border-border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary"
          />
        </div>



        <div className="flex gap-3 pt-2">
          <button
            type="submit"
            disabled={isPending}
            className="flex-1 px-6 py-2 bg-primary text-white rounded-md text-sm font-medium hover:bg-primary/85 disabled:opacity-50"
          >
            {isPending ? 'En cours…' : 'Créer'}
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
