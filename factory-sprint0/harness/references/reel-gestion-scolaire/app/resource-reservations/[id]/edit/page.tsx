import { auth } from '@clerk/nextjs/server'
import { redirect, notFound } from 'next/navigation'
import { resourceReservationService } from '@/lib/services/resource-reservation.service'
import { digitalResourceService } from '@/lib/services/digital-resource.service'
import ResourceReservationEditClient from './page-client'

export const dynamic = 'force-dynamic'

export default async function ResourceReservationEditPage({ params }: { params: Promise<{ id: string }> }) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const { id } = await params
  const item = await resourceReservationService.getById(userId, id)
  if (!item) notFound()
  const digitalResourceOptions = await digitalResourceService.getAll(userId)
  return <ResourceReservationEditClient item={item} digitalResourceOptions={digitalResourceOptions} />
}
