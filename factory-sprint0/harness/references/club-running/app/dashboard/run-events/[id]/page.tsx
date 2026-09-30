import { auth } from '@clerk/nextjs/server'
import { redirect, notFound } from 'next/navigation'
import DashboardRunEventsIdClient from './page-client'
import { runEventService } from '@/lib/services/run-event.service'

export const dynamic = 'force-dynamic'

export default async function DashboardRunEventsIdPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const item = await runEventService.getByIdWithRelations(userId, id)
  if (!item) notFound()
  return <DashboardRunEventsIdClient item={item} />
}
