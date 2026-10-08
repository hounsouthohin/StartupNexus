import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import DashboardManagersClient from './page-client'
import { managerService } from '@/lib/services/manager.service'

export const dynamic = 'force-dynamic'

export default async function DashboardManagersPage() {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const items = await managerService.getAllWithRelations(userId)
  return <DashboardManagersClient items={items} />
}
