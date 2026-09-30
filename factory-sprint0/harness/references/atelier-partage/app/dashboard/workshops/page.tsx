import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import DashboardWorkshopsClient from './page-client'
import { workshopService } from '@/lib/services/workshop.service'

export const dynamic = 'force-dynamic'

export default async function DashboardWorkshopsPage() {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const items = await workshopService.getAllWithRelations(userId)
  return <DashboardWorkshopsClient items={items} />
}
