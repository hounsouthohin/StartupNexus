import { auth } from '@clerk/nextjs/server'
import { redirect, notFound } from 'next/navigation'
import DashboardVehiclesIdClient from './page-client'
import { vehicleService } from '@/lib/services/vehicle.service'

export const dynamic = 'force-dynamic'

export default async function DashboardVehiclesIdPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const item = await vehicleService.getByIdWithRelations(userId, id)
  if (!item) notFound()
  return <DashboardVehiclesIdClient item={item} />
}
