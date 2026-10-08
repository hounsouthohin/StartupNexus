import { auth } from '@clerk/nextjs/server'
import { redirect, notFound } from 'next/navigation'
import ExamsIdClient from './page-client'
import { examService } from '@/lib/services/exam.service'
import { getCurrentRole } from '@/lib/auth-role'

export const dynamic = 'force-dynamic'

export default async function ExamsIdPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const _role = await getCurrentRole()
  const item = _role === 'direction'
    ? await examService.getByIdWithRelationsAsAdmin(id)
    : await examService.getByIdWithRelations(userId, id)
  if (!item) notFound()
  return <ExamsIdClient item={item} />
}
