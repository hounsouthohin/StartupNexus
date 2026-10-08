import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import MembersNewClient from './page-client'
import { subscriptionService } from '@/lib/services/subscription.service'

export const dynamic = 'force-dynamic'

export default async function MembersNewPage() {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const subscriptionOptions = await subscriptionService.getAll(userId)
  return <MembersNewClient subscriptionOptions={subscriptionOptions} />
}
