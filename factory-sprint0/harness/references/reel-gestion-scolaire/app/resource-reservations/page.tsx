import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import ResourceReservationsClient from './page-client'
import { resourceReservationService } from '@/lib/services/resource-reservation.service'
import { getCurrentRole } from '@/lib/auth-role'

export const dynamic = 'force-dynamic'

export default async function ResourceReservationsPage() {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const _role = await getCurrentRole()
  const items = _role === 'direction'
    ? await resourceReservationService.getAllAsAdmin()
    : await resourceReservationService.getAllWithRelations(userId)
  return <ResourceReservationsClient items={items} />
}
