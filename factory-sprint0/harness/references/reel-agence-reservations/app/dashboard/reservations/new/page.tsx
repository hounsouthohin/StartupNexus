import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import DashboardReservationsNewClient from './page-client'
import { getCurrentRole } from '@/lib/auth-role'
import { providerService } from '@/lib/services/provider.service'
import { managerService } from '@/lib/services/manager.service'

export const dynamic = 'force-dynamic'

export default async function DashboardReservationsNewPage() {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  if ((await getCurrentRole()) === 'admin') redirect('/dashboard/reservations')
  const providerOptions = await providerService.getAll(userId)
  const managerOptions = await managerService.getAll(userId)
  return <DashboardReservationsNewClient providerOptions={providerOptions} managerOptions={managerOptions} />
}
