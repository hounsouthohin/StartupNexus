import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import DashboardSubscriptionsClient from './page-client'
import { subscriptionService } from '@/lib/services/subscription.service'

export const dynamic = 'force-dynamic'

export default async function DashboardSubscriptionsPage() {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const items = await subscriptionService.getAllWithRelations(userId)
  return <DashboardSubscriptionsClient items={items} />
}
