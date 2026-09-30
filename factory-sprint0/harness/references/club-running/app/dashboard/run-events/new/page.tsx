import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import DashboardRunEventsNewClient from './page-client'

export const dynamic = 'force-dynamic'

export default async function DashboardRunEventsNewPage() {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  return <DashboardRunEventsNewClient />
}
