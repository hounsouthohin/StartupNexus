import { auth } from '@clerk/nextjs/server'
import { redirect, notFound } from 'next/navigation'
import { continuousAssessmentService } from '@/lib/services/continuous-assessment.service'
import { courseService } from '@/lib/services/course.service'
import ContinuousAssessmentEditClient from './page-client'

export const dynamic = 'force-dynamic'

export default async function ContinuousAssessmentEditPage({ params }: { params: Promise<{ id: string }> }) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const { id } = await params
  const item = await continuousAssessmentService.getById(userId, id)
  if (!item) notFound()
  const courseOptions = await courseService.getAll(userId)
  return <ContinuousAssessmentEditClient item={item} courseOptions={courseOptions} />
}
