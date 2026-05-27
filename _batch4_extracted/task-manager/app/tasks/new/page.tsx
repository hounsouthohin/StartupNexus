import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import TasksNewClient from './page-client'

export const dynamic = 'force-dynamic'

export default async function TasksNewPage() {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  return <TasksNewClient />
}
