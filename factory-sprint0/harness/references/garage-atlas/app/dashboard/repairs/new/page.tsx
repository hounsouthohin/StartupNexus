import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import DashboardRepairsNewClient from './page-client'
import { getCurrentRole } from '@/lib/auth-role'
import { vehicleService } from '@/lib/services/vehicle.service'

export const dynamic = 'force-dynamic'

export default async function DashboardRepairsNewPage() {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  if ((await getCurrentRole()) === 'owner') redirect('/dashboard/repairs')
  const vehicleOptions = await vehicleService.getAll(userId)
  return <DashboardRepairsNewClient vehicleOptions={vehicleOptions} />
}
