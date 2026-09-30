import Link from 'next/link'
import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import { repairService } from '@/lib/services/repair.service'

export const dynamic = 'force-dynamic'

export default async function DashboardPage() {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')

  const repairs = await repairService.getAll(userId, 1, 100000)

  const kpi0 = repairs.filter(x => String(x.status) === 'pending').length
  const kpi1 = repairs.filter(x => String(x.status) === 'in_progress').length
  const kpi2 = repairs.filter(x => String(x.createdAt) === 'current_month').reduce((s, x) => s + (Number(x.amountCharged) || 0), 0)

  return (
    <main className="container mx-auto p-8">
      <h1 className="text-2xl font-bold text-foreground mb-6">Tableau de bord</h1>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
        <div className="bg-card border border-border rounded-lg p-6">
          <p className="text-sm text-muted-foreground mb-1">Réparations en attente</p>
          <p className="text-3xl font-bold text-foreground">{kpi0}</p>
        </div>
        <div className="bg-card border border-border rounded-lg p-6">
          <p className="text-sm text-muted-foreground mb-1">Réparations en cours</p>
          <p className="text-3xl font-bold text-foreground">{kpi1}</p>
        </div>
        <div className="bg-card border border-border rounded-lg p-6">
          <p className="text-sm text-muted-foreground mb-1">Total facturé ce mois-ci</p>
          <p className="text-3xl font-bold text-foreground">{kpi2}</p>
        </div>
      </div>
      
      <div className="flex flex-wrap gap-3">
        <Link href="/dashboard/clients" className="px-4 py-2 bg-primary text-white rounded-md text-sm font-medium hover:bg-primary/85">Gérer Clients</Link>
        <Link href="/dashboard/vehicles" className="px-4 py-2 bg-primary text-white rounded-md text-sm font-medium hover:bg-primary/85">Gérer Véhicules</Link>
        <Link href="/dashboard/repairs" className="px-4 py-2 bg-primary text-white rounded-md text-sm font-medium hover:bg-primary/85">Gérer Réparations</Link>
      </div>
    </main>
  )
}
