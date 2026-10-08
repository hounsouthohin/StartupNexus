import { auth } from '@clerk/nextjs/server'
import { redirect, notFound } from 'next/navigation'
import StudentRecordsIdClient from './page-client'
import { studentRecordService } from '@/lib/services/student-record.service'
import { getCurrentRole } from '@/lib/auth-role'

export const dynamic = 'force-dynamic'

export default async function StudentRecordsIdPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const _role = await getCurrentRole()
  const item = _role === 'direction'
    ? await studentRecordService.getByIdWithRelationsAsAdmin(id)
    : await studentRecordService.getByIdWithRelations(userId, id)
  if (!item) notFound()
  return <StudentRecordsIdClient item={item} />
}
