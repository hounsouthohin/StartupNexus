'use client'

import Link from 'next/link'
import type { SerializedRequest } from '@/lib/types'
import { formatDate } from '@/lib/utils'
import { deleteRequest } from '@/app/requests/actions'
import { transitionRequest } from '@/app/requests/actions'

const FIELD_VALUE_LABELS: Record<string, Record<string, string>> = {"priority": {"low": "Basse", "normal": "Normale", "high": "Haute"}, "status": {"new": "Nouvelle", "in_progress": "En cours", "resolved": "Résolue"}};
// Machine à états (type I) : transitions permises + champs captés à la transition.
const FLOW_TRANSITIONS: Record<string, string[]> = {"in_progress": ["resolved"], "new": ["in_progress"], "resolved": []}
const FLOW_LABELS: Record<string, string> = {"in_progress": "En cours", "new": "Nouvelle", "resolved": "Résolue"}
const FLOW_STATE_FIELDS: Record<string, string[]> = {}
const FLOW_FIELD_LABELS: Record<string, string> = {}

interface RequestsIdClientProps {
  item: SerializedRequest
}

export default function RequestsIdClient({ item }: RequestsIdClientProps) {
  const handleDelete = async () => {
    if (!confirm('Supprimer cet élément ?')) return
    await deleteRequest(item.id)
  }

  return (
    <main className="container mx-auto p-6 max-w-2xl">
      <div className="flex items-center gap-3 mb-6">
        <Link href="/requests" className="text-muted-foreground hover:text-foreground">←</Link>
        <h1 className="text-2xl font-bold text-foreground">Demande</h1>
      </div>


      <div className="bg-card rounded-lg border-2 border-border overflow-hidden">
        <dl className="divide-y divide-border">
          <div className="px-6 py-4 grid grid-cols-3 gap-4">
            <dt className="text-sm font-medium text-muted-foreground">Titre</dt>
            <dd className="text-sm text-foreground col-span-2">
              {String(item.title ?? '—')}
            </dd>
          </div>
          <div className="px-6 py-4 grid grid-cols-3 gap-4">
            <dt className="text-sm font-medium text-muted-foreground">Description</dt>
            <dd className="text-sm text-foreground col-span-2">
              {String(item.description ?? '—')}
            </dd>
          </div>
          <div className="px-6 py-4 grid grid-cols-3 gap-4">
            <dt className="text-sm font-medium text-muted-foreground">Priorité</dt>
            <dd className="text-sm text-foreground col-span-2">
              {(FIELD_VALUE_LABELS['priority'] ?? {})[String(item.priority)] ?? String(item.priority ?? '—')}
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
        <div className="mt-6 bg-card rounded-lg border-2 border-border p-6">
          <p className="text-sm font-medium text-foreground mb-3">Faire évoluer l&apos;état</p>
          <div className="space-y-3">
            {(FLOW_TRANSITIONS[item.status] ?? []).map(_target => (
              <form key={_target} action={transitionRequest.bind(null, item.id, _target)} className="flex items-end gap-3">
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
          href={`/requests/${item.id}/edit`}
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
          href="/requests"
          className="px-4 py-2 border border-border rounded-md text-sm font-medium text-foreground hover:bg-muted/50"
        >
          Retour
        </Link>
      </div>
    </main>
  )
}
