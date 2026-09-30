import { notFound } from 'next/navigation'
import RunEventsIdClient from './page-client'
import { runEventService } from '@/lib/services/run-event.service'

export const dynamic = 'force-dynamic'

export default async function RunEventsIdPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params
  const item = await runEventService.getPublicByIdWithRelations(id)
  if (!item) notFound()
  return <RunEventsIdClient item={item} />
}
