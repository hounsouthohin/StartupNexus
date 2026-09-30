import { auth } from '@clerk/nextjs/server'
import { redirect, notFound } from 'next/navigation'
import { repairService } from '@/lib/services/repair.service'
import { vehicleService } from '@/lib/services/vehicle.service'
import RepairEditClient from './page-client'

export const dynamic = 'force-dynamic'

export default async function RepairEditPage({ params }: { params: Promise<{ id: string }> }) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const { id } = await params
  const item = await repairService.getById(userId, id)
  if (!item) notFound()
  const vehicleOptions = await vehicleService.getAll(userId)
  return <RepairEditClient item={item} vehicleOptions={vehicleOptions} />
}
