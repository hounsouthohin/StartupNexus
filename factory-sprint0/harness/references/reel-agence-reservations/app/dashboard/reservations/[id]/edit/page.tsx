import { auth } from '@clerk/nextjs/server'
import { redirect, notFound } from 'next/navigation'
import { reservationService } from '@/lib/services/reservation.service'
import { providerService } from '@/lib/services/provider.service'
import { managerService } from '@/lib/services/manager.service'
import ReservationEditClient from './page-client'

export const dynamic = 'force-dynamic'

export default async function ReservationEditPage({ params }: { params: Promise<{ id: string }> }) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const { id } = await params
  const item = await reservationService.getById(userId, id)
  if (!item) notFound()
  const providerOptions = await providerService.getAll(userId)
  const managerOptions = await managerService.getAll(userId)
  return <ReservationEditClient item={item} providerOptions={providerOptions} managerOptions={managerOptions} />
}
