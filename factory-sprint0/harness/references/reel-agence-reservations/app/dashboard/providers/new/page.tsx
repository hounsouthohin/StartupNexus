import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import DashboardProvidersNewClient from './page-client'
import { managerService } from '@/lib/services/manager.service'

export const dynamic = 'force-dynamic'

export default async function DashboardProvidersNewPage() {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const managerOptions = await managerService.getAll(userId)
  return <DashboardProvidersNewClient managerOptions={managerOptions} />
}
