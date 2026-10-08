import CoursesClient from './page-client'
import { courseService } from '@/lib/services/course.service'

export const dynamic = 'force-dynamic'

export default async function CoursesPage() {
  const items = await courseService.getPublicAll()
  return <CoursesClient items={items} />
}
