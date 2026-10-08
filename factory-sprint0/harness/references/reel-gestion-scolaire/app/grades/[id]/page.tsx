import { auth } from '@clerk/nextjs/server'
import { redirect, notFound } from 'next/navigation'
import GradesIdClient from './page-client'
import { gradeService } from '@/lib/services/grade.service'
import { getCurrentRole } from '@/lib/auth-role'

export const dynamic = 'force-dynamic'

export default async function GradesIdPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const _role = await getCurrentRole()
  const item = _role === 'direction'
    ? await gradeService.getByIdWithRelationsAsAdmin(id)
    : await gradeService.getByIdWithRelations(userId, id)
  if (!item) notFound()
  return <GradesIdClient item={item} />
}
