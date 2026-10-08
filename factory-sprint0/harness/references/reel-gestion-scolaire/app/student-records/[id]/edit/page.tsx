import { auth } from '@clerk/nextjs/server'
import { redirect, notFound } from 'next/navigation'
import { studentRecordService } from '@/lib/services/student-record.service'
import { courseService } from '@/lib/services/course.service'
import { internshipService } from '@/lib/services/internship.service'
import { foreignExchangeService } from '@/lib/services/foreign-exchange.service'
import { projectService } from '@/lib/services/project.service'
import { continuousAssessmentService } from '@/lib/services/continuous-assessment.service'
import { examService } from '@/lib/services/exam.service'
import { defenseService } from '@/lib/services/defense.service'
import StudentRecordEditClient from './page-client'

export const dynamic = 'force-dynamic'

export default async function StudentRecordEditPage({ params }: { params: Promise<{ id: string }> }) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const { id } = await params
  const item = await studentRecordService.getByIdWithRelations(userId, id)
  if (!item) notFound()
  const courseOptions = await courseService.getAll(userId)
  const internshipOptions = await internshipService.getAll(userId)
  const foreignExchangeOptions = await foreignExchangeService.getAll(userId)
  const projectOptions = await projectService.getAll(userId)
  const continuousAssessmentOptions = await continuousAssessmentService.getAll(userId)
  const examOptions = await examService.getAll(userId)
  const defenseOptions = await defenseService.getAll(userId)
  return <StudentRecordEditClient item={item} courseOptions={courseOptions} internshipOptions={internshipOptions} foreignExchangeOptions={foreignExchangeOptions} projectOptions={projectOptions} continuousAssessmentOptions={continuousAssessmentOptions} examOptions={examOptions} defenseOptions={defenseOptions} />
}
