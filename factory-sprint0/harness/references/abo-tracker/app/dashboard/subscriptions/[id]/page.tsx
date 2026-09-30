import { auth } from '@clerk/nextjs/server'
import { redirect, notFound } from 'next/navigation'
import DashboardSubscriptionsIdClient from './page-client'
import { subscriptionService } from '@/lib/services/subscription.service'

export const dynamic = 'force-dynamic'

export default async function DashboardSubscriptionsIdPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const item = await subscriptionService.getByIdWithRelations(userId, id)
  if (!item) notFound()
  return <DashboardSubscriptionsIdClient item={item} />
}
