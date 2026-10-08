import { auth } from '@clerk/nextjs/server'
import { redirect, notFound } from 'next/navigation'
import { courseService } from '@/lib/services/course.service'
import CourseEditClient from './page-client'

export const dynamic = 'force-dynamic'

export default async function CourseEditPage({ params }: { params: Promise<{ id: string }> }) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const { id } = await params
  const item = await courseService.getById(userId, id)
  if (!item) notFound()
  return <CourseEditClient item={item} />
}
