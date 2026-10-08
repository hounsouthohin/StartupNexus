import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import AbsencesClient from './page-client'
import { absenceService } from '@/lib/services/absence.service'
import { getCurrentRole } from '@/lib/auth-role'

export const dynamic = 'force-dynamic'

export default async function AbsencesPage() {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const _role = await getCurrentRole()
  const items = _role === 'direction'
    ? await absenceService.getAllAsAdmin()
    : await absenceService.getAllWithRelations(userId)
  return <AbsencesClient items={items} />
}
