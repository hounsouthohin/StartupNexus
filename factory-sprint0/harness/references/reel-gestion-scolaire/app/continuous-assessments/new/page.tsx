import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import ContinuousAssessmentsNewClient from './page-client'
import { courseService } from '@/lib/services/course.service'

export const dynamic = 'force-dynamic'

export default async function ContinuousAssessmentsNewPage() {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const courseOptions = await courseService.getAll(userId)
  return <ContinuousAssessmentsNewClient courseOptions={courseOptions} />
}
