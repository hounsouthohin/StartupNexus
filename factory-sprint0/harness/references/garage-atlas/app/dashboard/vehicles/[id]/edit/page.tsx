import { auth } from '@clerk/nextjs/server'
import { redirect, notFound } from 'next/navigation'
import { vehicleService } from '@/lib/services/vehicle.service'
import { clientService } from '@/lib/services/client.service'
import VehicleEditClient from './page-client'

export const dynamic = 'force-dynamic'

export default async function VehicleEditPage({ params }: { params: Promise<{ id: string }> }) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const { id } = await params
  const item = await vehicleService.getById(userId, id)
  if (!item) notFound()
  const clientOptions = await clientService.getAll(userId)
  return <VehicleEditClient item={item} clientOptions={clientOptions} />
}
