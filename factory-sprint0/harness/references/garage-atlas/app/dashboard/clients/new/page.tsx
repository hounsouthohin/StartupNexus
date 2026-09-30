import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import DashboardClientsNewClient from './page-client'

export const dynamic = 'force-dynamic'

export default async function DashboardClientsNewPage() {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  return <DashboardClientsNewClient />
}
