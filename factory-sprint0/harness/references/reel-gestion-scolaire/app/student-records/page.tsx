import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import StudentRecordsClient from './page-client'
import { studentRecordService } from '@/lib/services/student-record.service'
import { getCurrentRole } from '@/lib/auth-role'

export const dynamic = 'force-dynamic'

export default async function StudentRecordsPage() {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const _role = await getCurrentRole()
  const items = _role === 'direction'
    ? await studentRecordService.getAllAsAdmin()
    : await studentRecordService.getAllWithRelations(userId)
  return <StudentRecordsClient items={items} />
}
