'use client'

import { useActionState } from 'react'
import Link from 'next/link'
import type { SerializedGrade } from '@/lib/types'
import type { SerializedCourse } from '@/lib/types'
import { updateGrade } from '@/app/grades/actions'


interface GradeEditClientProps {
  item: SerializedGrade
  courseOptions: SerializedCourse[]
}

export default function GradeEditClient({ item, courseOptions }: GradeEditClientProps) {
  const [error, formAction, isPending] = useActionState(
    async (_prev: unknown, formData: FormData) => {
      try { await updateGrade.bind(null, item.id)(formData); return null }
      catch (e) { return (e as Error).message }
    },
    null,
  )

  return (
    <main className="container mx-auto p-6 max-w-xl">
      <div className="flex items-center gap-3 mb-6">
        <Link href="/grades" className="text-muted-foreground hover:text-foreground">←</Link>
        <h1 className="text-2xl font-bold text-foreground">Modifier Note</h1>
      </div>

      {error && <p className="mb-4 text-sm text-red-600 bg-red-50 px-4 py-2 rounded">{error}</p>}

      <form action={formAction} className="space-y-4 bg-card rounded-lg shadow-sm border border-border p-6">
        <div>
          <label htmlFor="value" className="block text-sm font-medium text-foreground mb-1">
            Valeur
          </label>
          <input
            type="number"
            id="value"
            name="value"
            defaultValue={item.value != null ? String(item.value) : ''}
step="any"             className="w-full px-3 py-2 border border-border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary disabled:bg-muted disabled:text-muted-foreground"
          />
        </div>
        <div>
          <label htmlFor="studentId" className="block text-sm font-medium text-foreground mb-1">
            studentId
          </label>
          <input
            type="text"
            id="studentId"
            name="studentId"
            defaultValue={item.studentId != null ? String(item.studentId) : ''}
            className="w-full px-3 py-2 border border-border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary disabled:bg-muted disabled:text-muted-foreground"
          />
        </div>

        <div>
          <label htmlFor="courseId" className="block text-sm font-medium text-foreground mb-1">
            Course
          </label>
          <select
            id="courseId"
            name="courseId"
            defaultValue={item.courseId ?? ''}
            className="w-full px-3 py-2 border border-border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary disabled:bg-muted disabled:text-muted-foreground"
          >
            <option value="">Sélectionner…</option>
            {courseOptions.map(opt => (
              <option key={opt.id} value={opt.id}>{String(opt.name ?? opt.id)}</option>
            ))}
          </select>
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
            href="/grades"
            className="px-6 py-2 border border-border rounded-md text-sm font-medium text-foreground hover:bg-muted/50"
          >
            Annuler
          </Link>
        </div>
      </form>
    </main>
  )
}
