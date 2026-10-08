import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import ContinuousAssessmentsClient from './page-client'
import { continuousAssessmentService } from '@/lib/services/continuous-assessment.service'
import { getCurrentRole } from '@/lib/auth-role'

export const dynamic = 'force-dynamic'

export default async function ContinuousAssessmentsPage() {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const _role = await getCurrentRole()
  const items = _role === 'direction'
    ? await continuousAssessmentService.getAllAsAdmin()
    : await continuousAssessmentService.getAllWithRelations(userId)
  return <ContinuousAssessmentsClient items={items} />
}
