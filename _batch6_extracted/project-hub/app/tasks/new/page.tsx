import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import TasksNewClient from './page-client'
import { projectService } from '@/lib/services/project.service'

export const dynamic = 'force-dynamic'

export default async function TasksNewPage() {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const projectOptions = await projectService.getAll(userId)
  return <TasksNewClient projectOptions={projectOptions} />
}
