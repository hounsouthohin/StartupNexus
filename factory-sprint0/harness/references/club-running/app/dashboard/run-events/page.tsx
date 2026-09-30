import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import DashboardRunEventsClient from './page-client'
import { runEventService } from '@/lib/services/run-event.service'

export const dynamic = 'force-dynamic'

export default async function DashboardRunEventsPage() {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const items = await runEventService.getAllWithRelations(userId)
  return <DashboardRunEventsClient items={items} />
}
