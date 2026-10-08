import { auth } from '@clerk/nextjs/server'
import { redirect, notFound } from 'next/navigation'
import SubscriptionsIdClient from './page-client'
import { subscriptionService } from '@/lib/services/subscription.service'
import { getCurrentRole } from '@/lib/auth-role'

export const dynamic = 'force-dynamic'

export default async function SubscriptionsIdPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const _role = await getCurrentRole()
  const item = _role === 'admin'
    ? await subscriptionService.getByIdWithRelationsAsAdmin(id)
    : await subscriptionService.getByIdWithRelations(userId, id)
  if (!item) notFound()
  return <SubscriptionsIdClient item={item} />
}
