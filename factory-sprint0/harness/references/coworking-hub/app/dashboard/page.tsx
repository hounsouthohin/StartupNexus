import Link from 'next/link'
import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import { invoiceService } from '@/lib/services/invoice.service'
import { reservationService } from '@/lib/services/reservation.service'

export const dynamic = 'force-dynamic'

export default async function DashboardPage() {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')

  const invoices = await invoiceService.getAll(userId, 1, 100000)
  const reservations = await reservationService.getAllWithRelations(userId, 1, 100000)

  const kpi0 = invoices.filter(x => String(x.issueDate) === 'current_month').reduce((s, x) => s + (Number(x.amount) || 0), 0)
  const kpi1 = reservations.filter(x => String(x.status) === 'requested').length
  const kpi2 = invoices.filter(x => String(x.status) === 'pending').reduce((s, x) => s + (Number(x.amount) || 0), 0)

  return (
    <main className="container mx-auto p-8">
      <h1 className="text-2xl font-bold text-foreground mb-6">Tableau de bord</h1>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
        <div className="bg-card border border-border rounded-lg p-6">
          <p className="text-sm text-muted-foreground mb-1">Chiffre d'affaires du mois</p>
          <p className="text-3xl font-bold text-foreground">{kpi0}</p>
        </div>
        <div className="bg-card border border-border rounded-lg p-6">
          <p className="text-sm text-muted-foreground mb-1">Réservations en attente</p>
          <p className="text-3xl font-bold text-foreground">{kpi1}</p>
        </div>
        <div className="bg-card border border-border rounded-lg p-6">
          <p className="text-sm text-muted-foreground mb-1">Total des factures impayées</p>
          <p className="text-3xl font-bold text-foreground">{kpi2}</p>
        </div>
      </div>
      
      <div className="flex flex-wrap gap-3">
        <Link href="/spaces" className="px-4 py-2 bg-primary text-white rounded-md text-sm font-medium hover:bg-primary/85">Gérer Espaces</Link>
        <Link href="/dashboard/reservations" className="px-4 py-2 bg-primary text-white rounded-md text-sm font-medium hover:bg-primary/85">Gérer Réservations</Link>
        <Link href="/dashboard/invoices" className="px-4 py-2 bg-primary text-white rounded-md text-sm font-medium hover:bg-primary/85">Gérer Factures</Link>
      </div>
    </main>
  )
}
