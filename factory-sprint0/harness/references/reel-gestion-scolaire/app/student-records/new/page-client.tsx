'use client'

import { useActionState } from 'react'
import Link from 'next/link'
import { createStudentRecord } from '@/app/student-records/actions'
import type { SerializedCourse } from '@/lib/types'
import type { SerializedInternship } from '@/lib/types'
import type { SerializedForeignExchange } from '@/lib/types'
import type { SerializedProject } from '@/lib/types'
import type { SerializedContinuousAssessment } from '@/lib/types'
import type { SerializedExam } from '@/lib/types'
import type { SerializedDefense } from '@/lib/types'

interface StudentRecordsNewClientProps {
  courseOptions: SerializedCourse[], internshipOptions: SerializedInternship[], foreignExchangeOptions: SerializedForeignExchange[], projectOptions: SerializedProject[], continuousAssessmentOptions: SerializedContinuousAssessment[], examOptions: SerializedExam[], defenseOptions: SerializedDefense[]
}

export default function StudentRecordsNewClient({ courseOptions, internshipOptions, foreignExchangeOptions, projectOptions, continuousAssessmentOptions, examOptions, defenseOptions }: StudentRecordsNewClientProps) {
  const [error, formAction, isPending] = useActionState(
    async (_prev: unknown, formData: FormData) => {
      try { await createStudentRecord(formData); return null }
      catch (e) { return (e as Error).message }
    },
    null,
  )

  return (
    <main className="container mx-auto p-6 max-w-xl">
      <div className="flex items-center gap-3 mb-6">
        <Link href="/student-records" className="text-muted-foreground hover:text-foreground">←</Link>
        <h1 className="text-2xl font-bold text-foreground">Créer Dossier scolaire</h1>
      </div>

      {error && <p className="mb-4 text-sm text-red-600 bg-red-50 px-4 py-2 rounded">{error}</p>}

      <form action={formAction} className="space-y-4 bg-card rounded-lg shadow-sm border border-border p-6">
        <div>
          <label htmlFor="studentId" className="block text-sm font-medium text-foreground mb-1">
            ID Étudiant <span className="text-red-500">*</span>          </label>
          <input
            type="text"
            id="studentId"
            name="studentId"
required             className="w-full px-3 py-2 border border-border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary"
          />
        </div>


        <div>
          <span className="block text-sm font-medium text-foreground mb-1">Cours</span>
          <div className="max-h-40 overflow-y-auto border border-border rounded-md p-3 space-y-2">
            {courseOptions.length === 0 ? (
              <p className="text-sm text-muted-foreground">Aucun élément disponible.</p>
            ) : courseOptions.map(opt => (
              <label key={opt.id} className="flex items-center gap-2 text-sm text-foreground">
                <input
                  type="checkbox"
                  name="courseIds"
                  value={opt.id}
                  className="h-4 w-4 text-primary border-border rounded"
                />
                <span>{String(opt.name ?? opt.id)}</span>
              </label>
            ))}
          </div>
        </div>
        <div>
          <span className="block text-sm font-medium text-foreground mb-1">Stages</span>
          <div className="max-h-40 overflow-y-auto border border-border rounded-md p-3 space-y-2">
            {internshipOptions.length === 0 ? (
              <p className="text-sm text-muted-foreground">Aucun élément disponible.</p>
            ) : internshipOptions.map(opt => (
              <label key={opt.id} className="flex items-center gap-2 text-sm text-foreground">
                <input
                  type="checkbox"
                  name="internshipIds"
                  value={opt.id}
                  className="h-4 w-4 text-primary border-border rounded"
                />
                <span>{String(opt.companyName ?? opt.id)}</span>
              </label>
            ))}
          </div>
        </div>
        <div>
          <span className="block text-sm font-medium text-foreground mb-1">Séjours à l'étranger</span>
          <div className="max-h-40 overflow-y-auto border border-border rounded-md p-3 space-y-2">
            {foreignExchangeOptions.length === 0 ? (
              <p className="text-sm text-muted-foreground">Aucun élément disponible.</p>
            ) : foreignExchangeOptions.map(opt => (
              <label key={opt.id} className="flex items-center gap-2 text-sm text-foreground">
                <input
                  type="checkbox"
                  name="foreignExchangeIds"
                  value={opt.id}
                  className="h-4 w-4 text-primary border-border rounded"
                />
                <span>{String(opt.country ?? opt.id)}</span>
              </label>
            ))}
          </div>
        </div>
        <div>
          <span className="block text-sm font-medium text-foreground mb-1">Projets</span>
          <div className="max-h-40 overflow-y-auto border border-border rounded-md p-3 space-y-2">
            {projectOptions.length === 0 ? (
              <p className="text-sm text-muted-foreground">Aucun élément disponible.</p>
            ) : projectOptions.map(opt => (
              <label key={opt.id} className="flex items-center gap-2 text-sm text-foreground">
                <input
                  type="checkbox"
                  name="projectIds"
                  value={opt.id}
                  className="h-4 w-4 text-primary border-border rounded"
                />
                <span>{String(opt.title ?? opt.id)}</span>
              </label>
            ))}
          </div>
        </div>
        <div>
          <span className="block text-sm font-medium text-foreground mb-1">Contrôles continus</span>
          <div className="max-h-40 overflow-y-auto border border-border rounded-md p-3 space-y-2">
            {continuousAssessmentOptions.length === 0 ? (
              <p className="text-sm text-muted-foreground">Aucun élément disponible.</p>
            ) : continuousAssessmentOptions.map(opt => (
              <label key={opt.id} className="flex items-center gap-2 text-sm text-foreground">
                <input
                  type="checkbox"
                  name="continuousAssessmentIds"
                  value={opt.id}
                  className="h-4 w-4 text-primary border-border rounded"
                />
                <span>{String(opt.score ?? opt.id)}</span>
              </label>
            ))}
          </div>
        </div>
        <div>
          <span className="block text-sm font-medium text-foreground mb-1">Examens</span>
          <div className="max-h-40 overflow-y-auto border border-border rounded-md p-3 space-y-2">
            {examOptions.length === 0 ? (
              <p className="text-sm text-muted-foreground">Aucun élément disponible.</p>
            ) : examOptions.map(opt => (
              <label key={opt.id} className="flex items-center gap-2 text-sm text-foreground">
                <input
                  type="checkbox"
                  name="examIds"
                  value={opt.id}
                  className="h-4 w-4 text-primary border-border rounded"
                />
                <span>{String(opt.subject ?? opt.id)}</span>
              </label>
            ))}
          </div>
        </div>
        <div>
          <span className="block text-sm font-medium text-foreground mb-1">Soutenances</span>
          <div className="max-h-40 overflow-y-auto border border-border rounded-md p-3 space-y-2">
            {defenseOptions.length === 0 ? (
              <p className="text-sm text-muted-foreground">Aucun élément disponible.</p>
            ) : defenseOptions.map(opt => (
              <label key={opt.id} className="flex items-center gap-2 text-sm text-foreground">
                <input
                  type="checkbox"
                  name="defenseIds"
                  value={opt.id}
                  className="h-4 w-4 text-primary border-border rounded"
                />
                <span>{String(opt.topic ?? opt.id)}</span>
              </label>
            ))}
          </div>
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
            href="/student-records"
            className="px-6 py-2 border border-border rounded-md text-sm font-medium text-foreground hover:bg-muted/50"
          >
            Annuler
          </Link>
        </div>
      </form>
    </main>
  )
}
