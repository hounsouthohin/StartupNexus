import Link from 'next/link'
import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import { clientService } from '@/lib/services/client.service'
import { providerService } from '@/lib/services/provider.service'
import { reservationService } from '@/lib/services/reservation.service'
import { formatDate } from '@/lib/utils'

export const dynamic = 'force-dynamic'

export default async function DashboardPage() {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')

  const clients = await clientService.getAll(userId, 1, 100000)
  const providers = await providerService.getAll(userId, 1, 100000)
  const reservations = await reservationService.getAllWithRelations(userId, 1, 100000)

  const kpi0 = reservations.length
  const kpi1 = clients.length
  const kpi2 = providers.length
  const list0 = reservations.filter(x => String(x.status) === 'pending')
  const list1 = reservations.filter(x => new Date(x.date as string) > new Date())

  return (
    <main className="container mx-auto p-8">
      <h1 className="text-2xl font-bold text-foreground mb-6">Tableau de bord</h1>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
        <div className="bg-card border border-border rounded-lg p-6">
          <p className="text-sm text-muted-foreground mb-1">Total des réservations</p>
          <p className="text-3xl font-bold text-foreground">{kpi0}</p>
        </div>
        <div className="bg-card border border-border rounded-lg p-6">
          <p className="text-sm text-muted-foreground mb-1">Total des clients</p>
          <p className="text-3xl font-bold text-foreground">{kpi1}</p>
        </div>
        <div className="bg-card border border-border rounded-lg p-6">
          <p className="text-sm text-muted-foreground mb-1">Total des prestataires</p>
          <p className="text-3xl font-bold text-foreground">{kpi2}</p>
        </div>
      </div>
      <section className="mb-8">
        <h2 className="text-lg font-semibold text-foreground mb-3">Réservations en attente</h2>
        {list0.length === 0 ? (
          <p className="text-muted-foreground text-sm">Aucun élément.</p>
        ) : (
          <ul className="space-y-2">
            {list0.map(item => (
              <li key={item.id} className="bg-card border border-border rounded-md p-3 text-sm text-foreground">{formatDate(item.date)} — {String(item.status ?? '')}</li>
            ))}
          </ul>
        )}
      </section>
      <section className="mb-8">
        <h2 className="text-lg font-semibold text-foreground mb-3">Réservations à venir</h2>
        {list1.length === 0 ? (
          <p className="text-muted-foreground text-sm">Aucun élément.</p>
        ) : (
          <ul className="space-y-2">
            {list1.map(item => (
              <li key={item.id} className="bg-card border border-border rounded-md p-3 text-sm text-foreground">{formatDate(item.date)} — {String(item.status ?? '')}</li>
            ))}
          </ul>
        )}
      </section>
      <div className="flex flex-wrap gap-3">
        <Link href="/dashboard/reservations" className="px-4 py-2 bg-primary text-white rounded-md text-sm font-medium hover:bg-primary/85">Gérer Réservations</Link>
        <Link href="/dashboard/clients" className="px-4 py-2 bg-primary text-white rounded-md text-sm font-medium hover:bg-primary/85">Gérer Clients</Link>
        <Link href="/dashboard/providers" className="px-4 py-2 bg-primary text-white rounded-md text-sm font-medium hover:bg-primary/85">Gérer Prestataires</Link>
        <Link href="/dashboard/managers" className="px-4 py-2 bg-primary text-white rounded-md text-sm font-medium hover:bg-primary/85">Gérer Gestionnaires</Link>
        <Link href="/dashboard/alerts" className="px-4 py-2 bg-primary text-white rounded-md text-sm font-medium hover:bg-primary/85">Gérer Alertes</Link>
      </div>
    </main>
  )
}
