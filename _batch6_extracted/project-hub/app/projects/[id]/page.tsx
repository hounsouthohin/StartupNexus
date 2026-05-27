import { auth } from '@clerk/nextjs/server'
import { redirect, notFound } from 'next/navigation'
import ProjectsIdClient from './page-client'
import { projectService } from '@/lib/services/project.service'

export const dynamic = 'force-dynamic'

export default async function ProjectsIdPage({ params }: { params: { id: string } }) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const item = await projectService.getById(userId, params.id)
  if (!item) notFound()
  return <ProjectsIdClient item={item} />
}
