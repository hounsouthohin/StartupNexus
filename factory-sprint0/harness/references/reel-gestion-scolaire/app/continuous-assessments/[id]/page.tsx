import { auth } from '@clerk/nextjs/server'
import { redirect, notFound } from 'next/navigation'
import ContinuousAssessmentsIdClient from './page-client'
import { continuousAssessmentService } from '@/lib/services/continuous-assessment.service'
import { getCurrentRole } from '@/lib/auth-role'

export const dynamic = 'force-dynamic'

export default async function ContinuousAssessmentsIdPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const _role = await getCurrentRole()
  const item = _role === 'direction'
    ? await continuousAssessmentService.getByIdWithRelationsAsAdmin(id)
    : await continuousAssessmentService.getByIdWithRelations(userId, id)
  if (!item) notFound()
  return <ContinuousAssessmentsIdClient item={item} />
}
