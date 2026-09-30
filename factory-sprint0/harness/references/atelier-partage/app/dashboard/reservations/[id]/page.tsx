import { auth } from '@clerk/nextjs/server'
import { redirect, notFound } from 'next/navigation'
import DashboardReservationsIdClient from './page-client'
import { reservationService } from '@/lib/services/reservation.service'
import { getCurrentRole } from '@/lib/auth-role'

export const dynamic = 'force-dynamic'

export default async function DashboardReservationsIdPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const _role = await getCurrentRole()
  const item = _role === 'animator'
    ? await reservationService.getByIdWithRelationsAsAdmin(id)
    : await reservationService.getByIdWithRelations(userId, id)
  if (!item) notFound()
  return <DashboardReservationsIdClient item={item} />
}
