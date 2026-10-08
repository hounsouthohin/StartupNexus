import { auth } from '@clerk/nextjs/server'
import { redirect, notFound } from 'next/navigation'
import { gradeService } from '@/lib/services/grade.service'
import { courseService } from '@/lib/services/course.service'
import GradeEditClient from './page-client'

export const dynamic = 'force-dynamic'

export default async function GradeEditPage({ params }: { params: Promise<{ id: string }> }) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const { id } = await params
  const item = await gradeService.getById(userId, id)
  if (!item) notFound()
  const courseOptions = await courseService.getAll(userId)
  return <GradeEditClient item={item} courseOptions={courseOptions} />
}
