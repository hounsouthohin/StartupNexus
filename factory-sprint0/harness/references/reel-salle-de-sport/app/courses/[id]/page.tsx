import { notFound } from 'next/navigation'
import CoursesIdClient from './page-client'
import { courseService } from '@/lib/services/course.service'

export const dynamic = 'force-dynamic'

export default async function CoursesIdPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params
  const item = await courseService.getPublicByIdWithRelations(id)
  if (!item) notFound()
  return <CoursesIdClient item={item} />
}
