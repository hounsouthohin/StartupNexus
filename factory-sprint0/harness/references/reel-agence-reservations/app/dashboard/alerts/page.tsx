import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import DashboardAlertsClient from './page-client'
import { alertService } from '@/lib/services/alert.service'

export const dynamic = 'force-dynamic'

export default async function DashboardAlertsPage() {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const items = await alertService.getAllWithRelations(userId)
  return <DashboardAlertsClient items={items} />
}
