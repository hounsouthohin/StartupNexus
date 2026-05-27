import { auth } from '@clerk/nextjs/server'
import { redirect, notFound } from 'next/navigation'
import { taskService } from '@/lib/services/task.service'
import { projectService } from '@/lib/services/project.service'
import TaskEditClient from './page-client'

export const dynamic = 'force-dynamic'

export default async function TaskEditPage({ params }: { params: { id: string } }) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const item = await taskService.getById(userId, params.id)
  if (!item) notFound()
  const projectOptions = await projectService.getAll(userId)
  return <TaskEditClient item={item} projectOptions={projectOptions} />
}
