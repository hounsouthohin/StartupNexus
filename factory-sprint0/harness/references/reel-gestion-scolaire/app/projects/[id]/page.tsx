import { auth } from '@clerk/nextjs/server'
import { redirect, notFound } from 'next/navigation'
import ProjectsIdClient from './page-client'
import { projectService } from '@/lib/services/project.service'
import { getCurrentRole } from '@/lib/auth-role'

export const dynamic = 'force-dynamic'

export default async function ProjectsIdPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const _role = await getCurrentRole()
  const item = _role === 'direction'
    ? await projectService.getByIdWithRelationsAsAdmin(id)
    : await projectService.getByIdWithRelations(userId, id)
  if (!item) notFound()
  return <ProjectsIdClient item={item} />
}
