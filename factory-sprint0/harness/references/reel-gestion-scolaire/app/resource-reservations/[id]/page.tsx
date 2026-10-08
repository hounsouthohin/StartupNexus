import { auth } from '@clerk/nextjs/server'
import { redirect, notFound } from 'next/navigation'
import ResourceReservationsIdClient from './page-client'
import { resourceReservationService } from '@/lib/services/resource-reservation.service'
import { getCurrentRole } from '@/lib/auth-role'

export const dynamic = 'force-dynamic'

export default async function ResourceReservationsIdPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const _role = await getCurrentRole()
  const item = _role === 'direction'
    ? await resourceReservationService.getByIdWithRelationsAsAdmin(id)
    : await resourceReservationService.getByIdWithRelations(userId, id)
  if (!item) notFound()
  return <ResourceReservationsIdClient item={item} />
}
