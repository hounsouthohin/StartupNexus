import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import DashboardVehiclesClient from './page-client'
import { vehicleService } from '@/lib/services/vehicle.service'

export const dynamic = 'force-dynamic'

export default async function DashboardVehiclesPage() {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const items = await vehicleService.getAllWithRelations(userId)
  return <DashboardVehiclesClient items={items} />
}
