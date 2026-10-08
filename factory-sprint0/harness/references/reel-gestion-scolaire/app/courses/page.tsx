import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import CoursesClient from './page-client'
import { courseService } from '@/lib/services/course.service'
import { getCurrentRole } from '@/lib/auth-role'

export const dynamic = 'force-dynamic'

export default async function CoursesPage() {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const _role = await getCurrentRole()
  const items = _role === 'direction'
    ? await courseService.getAllAsAdmin()
    : await courseService.getAll(userId)
  return <CoursesClient items={items} />
}
