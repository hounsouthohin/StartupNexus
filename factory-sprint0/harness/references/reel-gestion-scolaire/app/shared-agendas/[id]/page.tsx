import { auth } from '@clerk/nextjs/server'
import { redirect, notFound } from 'next/navigation'
import SharedAgendasIdClient from './page-client'
import { sharedAgendaService } from '@/lib/services/shared-agenda.service'
import { getCurrentRole } from '@/lib/auth-role'

export const dynamic = 'force-dynamic'

export default async function SharedAgendasIdPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const _role = await getCurrentRole()
  const item = _role === 'direction'
    ? await sharedAgendaService.getByIdAsAdmin(id)
    : await sharedAgendaService.getById(userId, id)
  if (!item) notFound()
  return <SharedAgendasIdClient item={item} />
}
