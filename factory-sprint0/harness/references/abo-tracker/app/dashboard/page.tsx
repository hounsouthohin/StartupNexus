import Link from 'next/link'
import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import { subscriptionService } from '@/lib/services/subscription.service'
import { formatDate } from '@/lib/utils'

export const dynamic = 'force-dynamic'

export default async function DashboardPage() {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')

  const subscriptions = await subscriptionService.getAll(userId, 1, 100000)

  const kpi0 = subscriptions.filter(x => String(x.status) === 'active').reduce((s, x) => s + (Number(x.monthlyPrice) || 0), 0)
  const kpi1 = subscriptions.filter(x => String(x.status) === 'active').length
  const kpi2 = subscriptions.filter(x => String(x.status) === 'paused').length
  const kpi3 = subscriptions.filter(x => String(x.status) === 'cancelled').length
  const list0 = subscriptions.filter(x => { const _d = new Date(x.nextBillingDate as string); const _now = new Date(); const _lim = new Date(); _lim.setDate(_now.getDate() + 7); return _d >= _now && _d <= _lim })

  return (
    <main className="container mx-auto p-8">
      <h1 className="text-2xl font-bold text-foreground mb-6">Tableau de bord</h1>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
        <div className="bg-card border border-border rounded-lg p-6">
          <p className="text-sm text-muted-foreground mb-1">Total mensuel des abonnements actifs</p>
          <p className="text-3xl font-bold text-foreground">{kpi0}</p>
        </div>
        <div className="bg-card border border-border rounded-lg p-6">
          <p className="text-sm text-muted-foreground mb-1">Nombre d'abonnements actifs</p>
          <p className="text-3xl font-bold text-foreground">{kpi1}</p>
        </div>
        <div className="bg-card border border-border rounded-lg p-6">
          <p className="text-sm text-muted-foreground mb-1">Nombre d'abonnements en pause</p>
          <p className="text-3xl font-bold text-foreground">{kpi2}</p>
        </div>
        <div className="bg-card border border-border rounded-lg p-6">
          <p className="text-sm text-muted-foreground mb-1">Nombre d'abonnements résiliés</p>
          <p className="text-3xl font-bold text-foreground">{kpi3}</p>
        </div>
      </div>
      <section className="mb-8">
        <h2 className="text-lg font-semibold text-foreground mb-3">Abonnements avec prélèvement dans les 7 prochains jours</h2>
        {list0.length === 0 ? (
          <p className="text-muted-foreground text-sm">Aucun élément.</p>
        ) : (
          <ul className="space-y-2">
            {list0.map(item => (
              <li key={item.id} className="bg-card border border-border rounded-md p-3 text-sm text-foreground">{String(item.name ?? '')} — {formatDate(item.nextBillingDate)}</li>
            ))}
          </ul>
        )}
      </section>
      <div className="flex flex-wrap gap-3">
        <Link href="/dashboard/subscriptions" className="px-4 py-2 bg-primary text-white rounded-md text-sm font-medium hover:bg-primary/85">Gérer Abonnements</Link>
        <Link href="/dashboard/categories" className="px-4 py-2 bg-primary text-white rounded-md text-sm font-medium hover:bg-primary/85">Gérer Catégories</Link>
      </div>
    </main>
  )
}
