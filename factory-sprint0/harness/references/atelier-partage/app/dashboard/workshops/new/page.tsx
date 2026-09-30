import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import DashboardWorkshopsNewClient from './page-client'
import { domainService } from '@/lib/services/domain.service'

export const dynamic = 'force-dynamic'

export default async function DashboardWorkshopsNewPage() {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const domainOptions = await domainService.getAll(userId)
  return <DashboardWorkshopsNewClient domainOptions={domainOptions} />
}
