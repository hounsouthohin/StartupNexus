import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import ProjectsClient from './page-client'
import { projectService } from '@/lib/services/project.service'

export const dynamic = 'force-dynamic'

export default async function ProjectsPage() {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const items = await projectService.getAll(userId)
  return <ProjectsClient items={items} />
}
