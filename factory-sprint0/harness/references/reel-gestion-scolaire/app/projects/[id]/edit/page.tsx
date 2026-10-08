import { auth } from '@clerk/nextjs/server'
import { redirect, notFound } from 'next/navigation'
import { projectService } from '@/lib/services/project.service'
import ProjectEditClient from './page-client'

export const dynamic = 'force-dynamic'

export default async function ProjectEditPage({ params }: { params: Promise<{ id: string }> }) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const { id } = await params
  const item = await projectService.getById(userId, id)
  if (!item) notFound()
  return <ProjectEditClient item={item} />
}
