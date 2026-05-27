import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import TasksClient from './page-client'
import { taskService } from '@/lib/services/task.service'

export const dynamic = 'force-dynamic'

export default async function TasksPage() {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const items = await taskService.getAllWithRelations(userId)
  return <TasksClient items={items} />
}
