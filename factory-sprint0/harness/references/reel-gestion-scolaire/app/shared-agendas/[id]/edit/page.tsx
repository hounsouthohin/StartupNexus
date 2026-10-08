import { auth } from '@clerk/nextjs/server'
import { redirect, notFound } from 'next/navigation'
import { sharedAgendaService } from '@/lib/services/shared-agenda.service'
import SharedAgendaEditClient from './page-client'

export const dynamic = 'force-dynamic'

export default async function SharedAgendaEditPage({ params }: { params: Promise<{ id: string }> }) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const { id } = await params
  const item = await sharedAgendaService.getById(userId, id)
  if (!item) notFound()
  return <SharedAgendaEditClient item={item} />
}
