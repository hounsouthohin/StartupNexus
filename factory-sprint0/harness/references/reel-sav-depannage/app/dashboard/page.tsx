import Link from 'next/link'
import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import { clientService } from '@/lib/services/client.service'
import { machineService } from '@/lib/services/machine.service'
import { interventionService } from '@/lib/services/intervention.service'
import { actionService } from '@/lib/services/action.service'

export const dynamic = 'force-dynamic'

export default async function DashboardPage() {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')

  const [clientItems, machineItems, interventionItems, actionItems] = await Promise.all([
    clientService.getAll(userId, 1, 100000),
    machineService.getAll(userId, 1, 100000),
    interventionService.getAll(userId, 1, 100000),
    actionService.getAll(userId, 1, 100000),
  ])

  const clientCount = clientItems.length
  const machineCount = machineItems.length
  const interventionCount = interventionItems.length
  const actionCount = actionItems.length

  return (
    <main className="container mx-auto p-8">
      <h1 className="text-2xl font-bold text-foreground mb-6">Tableau de bord</h1>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
        <div className="bg-card border border-border rounded-lg p-6">
          <p className="text-sm text-muted-foreground mb-1">Clients</p>
          <p className="text-3xl font-bold text-foreground mb-4">{clientCount}</p>
          <Link href="/clients" className="text-sm text-primary hover:underline">Gérer →</Link>
        </div>
        <div className="bg-card border border-border rounded-lg p-6">
          <p className="text-sm text-muted-foreground mb-1">Machines</p>
          <p className="text-3xl font-bold text-foreground mb-4">{machineCount}</p>
          <Link href="/machines" className="text-sm text-primary hover:underline">Gérer →</Link>
        </div>
        <div className="bg-card border border-border rounded-lg p-6">
          <p className="text-sm text-muted-foreground mb-1">Interventions</p>
          <p className="text-3xl font-bold text-foreground mb-4">{interventionCount}</p>
          <Link href="/interventions" className="text-sm text-primary hover:underline">Gérer →</Link>
        </div>
        <div className="bg-card border border-border rounded-lg p-6">
          <p className="text-sm text-muted-foreground mb-1">Actions</p>
          <p className="text-3xl font-bold text-foreground mb-4">{actionCount}</p>
          <Link href="/actions" className="text-sm text-primary hover:underline">Gérer →</Link>
        </div>
      </div>
    </main>
  )
}
