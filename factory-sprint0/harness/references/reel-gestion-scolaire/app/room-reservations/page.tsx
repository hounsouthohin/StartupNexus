import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import RoomReservationsClient from './page-client'
import { roomReservationService } from '@/lib/services/room-reservation.service'
import { getCurrentRole } from '@/lib/auth-role'

export const dynamic = 'force-dynamic'

export default async function RoomReservationsPage() {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const _role = await getCurrentRole()
  const items = _role === 'direction'
    ? await roomReservationService.getAllAsAdmin()
    : await roomReservationService.getAllWithRelations(userId)
  return <RoomReservationsClient items={items} />
}
