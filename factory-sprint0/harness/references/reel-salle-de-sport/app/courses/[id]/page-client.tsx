'use client'

import Link from 'next/link'
import type { SerializedCourse } from '@/lib/types'
import { formatDate } from '@/lib/utils'

interface CoursesIdClientProps {
  item: SerializedCourse
}

export default function CoursesIdClient({ item }: CoursesIdClientProps) {

  return (
    <main className="container mx-auto p-8 max-w-2xl">
      <div className="flex items-center gap-3 mb-6">
        <Link href="/courses" className="text-muted-foreground hover:text-foreground">←</Link>
        <h1 className="text-2xl font-bold text-foreground">{String(item.title ?? 'Cours')}</h1>
      </div>

      <div className="bg-card rounded-lg shadow-sm border border-border p-6 mb-4">
        <p className="text-sm font-medium text-muted-foreground mb-2">Description</p>
        <p className="text-foreground leading-relaxed whitespace-pre-wrap">{String(item.description ?? '')}</p>
      </div>

      <div className="bg-card rounded-lg shadow-sm border border-border overflow-hidden">
        <dl className="divide-y divide-border">
          <div className="px-6 py-4 grid grid-cols-3 gap-4">
            <dt className="text-sm font-medium text-muted-foreground">Horaire</dt>
            <dd className="text-sm text-foreground col-span-2">
              {formatDate(item.schedule)}
            </dd>
          </div>
        </dl>
      </div>


      <div className="mt-6 flex gap-3">
        <Link
          href="/courses"
          className="px-4 py-2 border border-border rounded-md text-sm font-medium text-foreground hover:bg-muted/50"
        >
          Retour
        </Link>
      </div>
    </main>
  )
}
