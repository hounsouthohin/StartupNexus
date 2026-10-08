import { auth } from '@clerk/nextjs/server'
import { redirect, notFound } from 'next/navigation'
import AbsencesIdClient from './page-client'
import { absenceService } from '@/lib/services/absence.service'
import { getCurrentRole } from '@/lib/auth-role'

export const dynamic = 'force-dynamic'

export default async function AbsencesIdPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const _role = await getCurrentRole()
  const item = _role === 'direction'
    ? await absenceService.getByIdWithRelationsAsAdmin(id)
    : await absenceService.getByIdWithRelations(userId, id)
  if (!item) notFound()
  return <AbsencesIdClient item={item} />
}
