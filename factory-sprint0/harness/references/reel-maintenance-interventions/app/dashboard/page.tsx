import Link from 'next/link'
import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import { interventionService } from '@/lib/services/intervention.service'
import { clientService } from '@/lib/services/client.service'
import { technicianService } from '@/lib/services/technician.service'
import { invoiceService } from '@/lib/services/invoice.service'

export const dynamic = 'force-dynamic'

export default async function DashboardPage() {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')

  const [interventionItems, clientItems, technicianItems, invoiceItems] = await Promise.all([
    interventionService.getAll(userId, 1, 100000),
    clientService.getAll(userId, 1, 100000),
    technicianService.getAll(userId, 1, 100000),
    invoiceService.getAll(userId, 1, 100000),
  ])

  const interventionCount = interventionItems.length
  const clientCount = clientItems.length
  const technicianCount = technicianItems.length
  const invoiceCount = invoiceItems.length

  return (
    <main className="container mx-auto p-8">
      <h1 className="text-2xl font-bold text-foreground mb-6">Tableau de bord</h1>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
        <div className="bg-card border border-border rounded-lg p-6">
          <p className="text-sm text-muted-foreground mb-1">Interventions</p>
          <p className="text-3xl font-bold text-foreground mb-4">{interventionCount}</p>
          <Link href="/interventions" className="text-sm text-primary hover:underline">Gérer →</Link>
        </div>
        <div className="bg-card border border-border rounded-lg p-6">
          <p className="text-sm text-muted-foreground mb-1">Clients</p>
          <p className="text-3xl font-bold text-foreground mb-4">{clientCount}</p>
          <Link href="/clients" className="text-sm text-primary hover:underline">Gérer →</Link>
        </div>
        <div className="bg-card border border-border rounded-lg p-6">
          <p className="text-sm text-muted-foreground mb-1">Techniciens</p>
          <p className="text-3xl font-bold text-foreground mb-4">{technicianCount}</p>
          <Link href="/technicians" className="text-sm text-primary hover:underline">Gérer →</Link>
        </div>
        <div className="bg-card border border-border rounded-lg p-6">
          <p className="text-sm text-muted-foreground mb-1">Factures</p>
          <p className="text-3xl font-bold text-foreground mb-4">{invoiceCount}</p>
          <Link href="/invoices" className="text-sm text-primary hover:underline">Gérer →</Link>
        </div>
      </div>
    </main>
  )
}
