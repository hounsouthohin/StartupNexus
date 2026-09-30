import Link from 'next/link'
import { runEventService } from '@/lib/services/run-event.service'
import { formatDate } from '@/lib/utils'

export const dynamic = 'force-dynamic'

export default async function HomePage() {
  const runEvents = await runEventService.getPublicAll(1, 100000)

  const list0 = runEvents.filter(x => new Date(x.dateTime as string) > new Date())

  return (
    <main className="container mx-auto p-8">
      
      <section className="mb-8">
        <h2 className="text-lg font-semibold text-foreground mb-3">Prochaines sorties</h2>
        {list0.length === 0 ? (
          <p className="text-muted-foreground text-sm">Aucun élément.</p>
        ) : (
          <ul className="space-y-2">
            {list0.map(item => (
              <li key={item.id} className="bg-card border border-border rounded-md p-4 text-sm text-foreground"><Link href={`/run-events/${item.id}`} className="font-medium text-primary hover:underline">{String(item.title ?? '')}</Link> — {formatDate(item.dateTime)} — {String(item.location ?? '')}</li>
            ))}
          </ul>
        )}
      </section>
    </main>
  )
}
