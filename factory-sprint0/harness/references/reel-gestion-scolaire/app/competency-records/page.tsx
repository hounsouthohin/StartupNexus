import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import CompetencyRecordsClient from './page-client'
import { competencyRecordService } from '@/lib/services/competency-record.service'
import { getCurrentRole } from '@/lib/auth-role'

export const dynamic = 'force-dynamic'

export default async function CompetencyRecordsPage() {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const _role = await getCurrentRole()
  const items = _role === 'direction'
    ? await competencyRecordService.getAllAsAdmin()
    : await competencyRecordService.getAllWithRelations(userId)
  return <CompetencyRecordsClient items={items} />
}
