import { auth } from '@clerk/nextjs/server'
import { redirect, notFound } from 'next/navigation'
import CompetencyRecordsIdClient from './page-client'
import { competencyRecordService } from '@/lib/services/competency-record.service'
import { getCurrentRole } from '@/lib/auth-role'

export const dynamic = 'force-dynamic'

export default async function CompetencyRecordsIdPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const _role = await getCurrentRole()
  const item = _role === 'direction'
    ? await competencyRecordService.getByIdWithRelationsAsAdmin(id)
    : await competencyRecordService.getByIdWithRelations(userId, id)
  if (!item) notFound()
  return <CompetencyRecordsIdClient item={item} />
}
