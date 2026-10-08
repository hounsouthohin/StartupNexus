import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import ProjectsClient from './page-client'
import { projectService } from '@/lib/services/project.service'
import { getCurrentRole } from '@/lib/auth-role'

export const dynamic = 'force-dynamic'

export default async function ProjectsPage() {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const _role = await getCurrentRole()
  const items = _role === 'direction'
    ? await projectService.getAllAsAdmin()
    : await projectService.getAllWithRelations(userId)
  return <ProjectsClient items={items} />
}
