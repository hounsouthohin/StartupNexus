import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import SubscriptionsNewClient from './page-client'

export const dynamic = 'force-dynamic'

export default async function SubscriptionsNewPage() {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  return <SubscriptionsNewClient />
}
