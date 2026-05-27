import { auth } from '@clerk/nextjs/server'
import { redirect, notFound } from 'next/navigation'
import TasksIdClient from './page-client'
import { taskService } from '@/lib/services/task.service'

export const dynamic = 'force-dynamic'

export default async function TasksIdPage({ params }: { params: { id: string } }) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const item = await taskService.getById(userId, params.id)
  if (!item) notFound()
  return <TasksIdClient item={item} />
}
