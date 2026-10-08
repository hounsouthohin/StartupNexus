import Link from 'next/link'
import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import { memberService } from '@/lib/services/member.service'
import { subscriptionService } from '@/lib/services/subscription.service'
import { courseService } from '@/lib/services/course.service'
import { reservationService } from '@/lib/services/reservation.service'
import { paymentService } from '@/lib/services/payment.service'

export const dynamic = 'force-dynamic'

export default async function DashboardPage() {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')

  const [memberItems, subscriptionItems, courseItems, reservationItems, paymentItems] = await Promise.all([
    memberService.getAll(userId, 1, 100000),
    subscriptionService.getAll(userId, 1, 100000),
    courseService.getAll(userId, 1, 100000),
    reservationService.getAll(userId, 1, 100000),
    paymentService.getAll(userId, 1, 100000),
  ])

  const memberCount = memberItems.length
  const subscriptionCount = subscriptionItems.length
  const courseCount = courseItems.length
  const reservationCount = reservationItems.length
  const paymentCount = paymentItems.length

  return (
    <main className="container mx-auto p-8">
      <h1 className="text-2xl font-bold text-foreground mb-6">Tableau de bord</h1>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
        <div className="bg-card border border-border rounded-lg p-6">
          <p className="text-sm text-muted-foreground mb-1">Membres</p>
          <p className="text-3xl font-bold text-foreground mb-4">{memberCount}</p>
          <Link href="/members" className="text-sm text-primary hover:underline">Gérer →</Link>
        </div>
        <div className="bg-card border border-border rounded-lg p-6">
          <p className="text-sm text-muted-foreground mb-1">Abonnements</p>
          <p className="text-3xl font-bold text-foreground mb-4">{subscriptionCount}</p>
          <Link href="/subscriptions" className="text-sm text-primary hover:underline">Gérer →</Link>
        </div>
        <div className="bg-card border border-border rounded-lg p-6">
          <p className="text-sm text-muted-foreground mb-1">Cours</p>
          <p className="text-3xl font-bold text-foreground mb-4">{courseCount}</p>
          <Link href="/courses" className="text-sm text-primary hover:underline">Gérer →</Link>
        </div>
        <div className="bg-card border border-border rounded-lg p-6">
          <p className="text-sm text-muted-foreground mb-1">Réservations</p>
          <p className="text-3xl font-bold text-foreground mb-4">{reservationCount}</p>
          <Link href="/reservations" className="text-sm text-primary hover:underline">Gérer →</Link>
        </div>
        <div className="bg-card border border-border rounded-lg p-6">
          <p className="text-sm text-muted-foreground mb-1">Paiements</p>
          <p className="text-3xl font-bold text-foreground mb-4">{paymentCount}</p>
          <Link href="/payments" className="text-sm text-primary hover:underline">Gérer →</Link>
        </div>
      </div>
    </main>
  )
}
