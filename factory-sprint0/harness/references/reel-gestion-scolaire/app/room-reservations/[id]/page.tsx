import { auth } from '@clerk/nextjs/server'
import { redirect, notFound } from 'next/navigation'
import RoomReservationsIdClient from './page-client'
import { roomReservationService } from '@/lib/services/room-reservation.service'
import { getCurrentRole } from '@/lib/auth-role'

export const dynamic = 'force-dynamic'

export default async function RoomReservationsIdPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const _role = await getCurrentRole()
  const item = _role === 'direction'
    ? await roomReservationService.getByIdWithRelationsAsAdmin(id)
    : await roomReservationService.getByIdWithRelations(userId, id)
  if (!item) notFound()
  return <RoomReservationsIdClient item={item} />
}
