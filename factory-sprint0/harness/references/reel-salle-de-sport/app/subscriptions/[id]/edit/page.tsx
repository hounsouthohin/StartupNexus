import { auth } from '@clerk/nextjs/server'
import { redirect, notFound } from 'next/navigation'
import { subscriptionService } from '@/lib/services/subscription.service'
import SubscriptionEditClient from './page-client'

export const dynamic = 'force-dynamic'

export default async function SubscriptionEditPage({ params }: { params: Promise<{ id: string }> }) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const { id } = await params
  const item = await subscriptionService.getById(userId, id)
  if (!item) notFound()
  return <SubscriptionEditClient item={item} />
}
