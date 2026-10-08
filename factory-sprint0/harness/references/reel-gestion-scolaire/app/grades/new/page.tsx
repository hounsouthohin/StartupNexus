import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import GradesNewClient from './page-client'
import { courseService } from '@/lib/services/course.service'

export const dynamic = 'force-dynamic'

export default async function GradesNewPage() {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const courseOptions = await courseService.getAll(userId)
  return <GradesNewClient courseOptions={courseOptions} />
}
