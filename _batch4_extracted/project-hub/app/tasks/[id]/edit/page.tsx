import { auth } from '@clerk/nextjs/server'
import { redirect, notFound } from 'next/navigation'
import { taskService } from '@/lib/services/task.service'
import TaskEditClient from './page-client'

export const dynamic = 'force-dynamic'

export default async function TaskEditPage({ params }: { params: { id: string } }) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const item = await taskService.getById(userId, params.id)
  if (!item) notFound()
  return <TaskEditClient item={item} />
}
