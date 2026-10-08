import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import RoomReservationsNewClient from './page-client'

export const dynamic = 'force-dynamic'

export default async function RoomReservationsNewPage() {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  return <RoomReservationsNewClient />
}
