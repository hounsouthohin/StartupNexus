import { auth } from '@clerk/nextjs/server'
import { redirect, notFound } from 'next/navigation'
import CoursesIdClient from './page-client'
import { courseService } from '@/lib/services/course.service'
import { getCurrentRole } from '@/lib/auth-role'

export const dynamic = 'force-dynamic'

export default async function CoursesIdPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const _role = await getCurrentRole()
  const item = _role === 'direction'
    ? await courseService.getByIdAsAdmin(id)
    : await courseService.getById(userId, id)
  if (!item) notFound()
  return <CoursesIdClient item={item} />
}
