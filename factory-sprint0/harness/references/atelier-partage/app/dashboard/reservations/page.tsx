import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import DashboardReservationsClient from './page-client'
import { reservationService } from '@/lib/services/reservation.service'
import { getCurrentRole } from '@/lib/auth-role'

export const dynamic = 'force-dynamic'

export default async function DashboardReservationsPage() {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const _role = await getCurrentRole()
  const items = _role === 'animator'
    ? await reservationService.getAllAsAdmin()
    : await reservationService.getAllWithRelations(userId)
  return <DashboardReservationsClient items={items} />
}
