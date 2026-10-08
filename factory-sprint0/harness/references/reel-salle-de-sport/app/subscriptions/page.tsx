import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import SubscriptionsClient from './page-client'
import { subscriptionService } from '@/lib/services/subscription.service'
import { getCurrentRole } from '@/lib/auth-role'

export const dynamic = 'force-dynamic'

export default async function SubscriptionsPage() {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const _role = await getCurrentRole()
  const items = _role === 'admin'
    ? await subscriptionService.getAllAsAdmin()
    : await subscriptionService.getAllWithRelations(userId)
  return <SubscriptionsClient items={items} />
}
