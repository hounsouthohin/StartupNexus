import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import SharedAgendasClient from './page-client'
import { sharedAgendaService } from '@/lib/services/shared-agenda.service'
import { getCurrentRole } from '@/lib/auth-role'

export const dynamic = 'force-dynamic'

export default async function SharedAgendasPage() {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const _role = await getCurrentRole()
  const items = _role === 'direction'
    ? await sharedAgendaService.getAllAsAdmin()
    : await sharedAgendaService.getAll(userId)
  return <SharedAgendasClient items={items} />
}
