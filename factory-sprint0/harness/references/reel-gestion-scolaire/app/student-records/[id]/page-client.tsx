'use client'

import Link from 'next/link'
import type { SerializedStudentRecord } from '@/lib/types'
import { formatDate } from '@/lib/utils'
import { deleteStudentRecord } from '@/app/student-records/actions'

interface StudentRecordsIdClientProps {
  item: SerializedStudentRecord
}

export default function StudentRecordsIdClient({ item }: StudentRecordsIdClientProps) {
  const handleDelete = async () => {
    if (!confirm('Supprimer cet élément ?')) return
    await deleteStudentRecord(item.id)
  }

  return (
    <main className="container mx-auto p-6 max-w-2xl">
      <div className="flex items-center gap-3 mb-6">
        <Link href="/student-records" className="text-muted-foreground hover:text-foreground">←</Link>
        <h1 className="text-2xl font-bold text-foreground">Dossier scolaire</h1>
      </div>

      {(item.courses ?? []).length > 0 && (
        <div className="flex flex-wrap gap-2 mb-4">
          {(item.courses ?? []).map(rel => (
            <span key={rel.id} className="inline-flex px-2 py-0.5 rounded-full text-xs font-medium bg-primary/10 text-primary">
              {String(rel.name ?? '')}
            </span>
          ))}
        </div>
      )}

      {(item.internships ?? []).length > 0 && (
        <div className="flex flex-wrap gap-2 mb-4">
          {(item.internships ?? []).map(rel => (
            <span key={rel.id} className="inline-flex px-2 py-0.5 rounded-full text-xs font-medium bg-primary/10 text-primary">
              {String(rel.companyName ?? '')}
            </span>
          ))}
        </div>
      )}

      {(item.foreignExchanges ?? []).length > 0 && (
        <div className="flex flex-wrap gap-2 mb-4">
          {(item.foreignExchanges ?? []).map(rel => (
            <span key={rel.id} className="inline-flex px-2 py-0.5 rounded-full text-xs font-medium bg-primary/10 text-primary">
              {String(rel.country ?? '')}
            </span>
          ))}
        </div>
      )}

      {(item.projects ?? []).length > 0 && (
        <div className="flex flex-wrap gap-2 mb-4">
          {(item.projects ?? []).map(rel => (
            <span key={rel.id} className="inline-flex px-2 py-0.5 rounded-full text-xs font-medium bg-primary/10 text-primary">
              {String(rel.title ?? '')}
            </span>
          ))}
        </div>
      )}

      {(item.continuousAssessments ?? []).length > 0 && (
        <div className="flex flex-wrap gap-2 mb-4">
          {(item.continuousAssessments ?? []).map(rel => (
            <span key={rel.id} className="inline-flex px-2 py-0.5 rounded-full text-xs font-medium bg-primary/10 text-primary">
              {String(rel.score ?? '')}
            </span>
          ))}
        </div>
      )}

      {(item.exams ?? []).length > 0 && (
        <div className="flex flex-wrap gap-2 mb-4">
          {(item.exams ?? []).map(rel => (
            <span key={rel.id} className="inline-flex px-2 py-0.5 rounded-full text-xs font-medium bg-primary/10 text-primary">
              {String(rel.subject ?? '')}
            </span>
          ))}
        </div>
      )}

      {(item.defenses ?? []).length > 0 && (
        <div className="flex flex-wrap gap-2 mb-4">
          {(item.defenses ?? []).map(rel => (
            <span key={rel.id} className="inline-flex px-2 py-0.5 rounded-full text-xs font-medium bg-primary/10 text-primary">
              {String(rel.topic ?? '')}
            </span>
          ))}
        </div>
      )}


      <div className="bg-card rounded-lg shadow-sm border border-border overflow-hidden">
        <dl className="divide-y divide-border">
          <div className="px-6 py-4 grid grid-cols-3 gap-4">
            <dt className="text-sm font-medium text-muted-foreground">ID Étudiant</dt>
            <dd className="text-sm text-foreground col-span-2">
              {String(item.studentId ?? '—')}
            </dd>
          </div>
        </dl>
      </div>


      <div className="mt-6 flex gap-3">
        <Link
          href={`/student-records/${item.id}/edit`}
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
          href="/student-records"
          className="px-4 py-2 border border-border rounded-md text-sm font-medium text-foreground hover:bg-muted/50"
        >
          Retour
        </Link>
      </div>
    </main>
  )
}
