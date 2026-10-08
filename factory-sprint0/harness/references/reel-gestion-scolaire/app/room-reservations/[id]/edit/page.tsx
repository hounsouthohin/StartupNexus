import { auth } from '@clerk/nextjs/server'
import { redirect, notFound } from 'next/navigation'
import { roomReservationService } from '@/lib/services/room-reservation.service'
import RoomReservationEditClient from './page-client'

export const dynamic = 'force-dynamic'

export default async function RoomReservationEditPage({ params }: { params: Promise<{ id: string }> }) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const { id } = await params
  const item = await roomReservationService.getById(userId, id)
  if (!item) notFound()
  return <RoomReservationEditClient item={item} />
}
