import Link from 'next/link'
import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import { requestService } from '@/lib/services/request.service'

export const dynamic = 'force-dynamic'

export default async function DashboardPage() {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')

  const [requestItems] = await Promise.all([
    requestService.getAll(userId, 1, 100000),
  ])

  const requestCount = requestItems.length

  return (
    <main className="container mx-auto p-8">
      <h1 className="text-2xl font-bold text-foreground mb-6">Tableau de bord</h1>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
        <div className="bg-card border border-border rounded-lg p-6">
          <p className="text-sm text-muted-foreground mb-1">Demandes</p>
          <p className="text-3xl font-bold text-foreground mb-4">{requestCount}</p>
          <Link href="/requests" className="text-sm text-primary hover:underline">Gérer →</Link>
        </div>
      </div>
    </main>
  )
}
