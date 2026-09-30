import { auth } from '@clerk/nextjs/server'
import { redirect, notFound } from 'next/navigation'
import { runEventService } from '@/lib/services/run-event.service'
import RunEventEditClient from './page-client'

export const dynamic = 'force-dynamic'

export default async function RunEventEditPage({ params }: { params: Promise<{ id: string }> }) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const { id } = await params
  const item = await runEventService.getById(userId, id)
  if (!item) notFound()
  return <RunEventEditClient item={item} />
}
