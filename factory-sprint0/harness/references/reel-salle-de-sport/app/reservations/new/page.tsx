import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import ReservationsNewClient from './page-client'
import { getCurrentRole } from '@/lib/auth-role'
import { memberService } from '@/lib/services/member.service'

export const dynamic = 'force-dynamic'

export default async function ReservationsNewPage() {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  if ((await getCurrentRole()) === 'admin') redirect('/reservations')
  const memberOptions = await memberService.getAll(userId)
  return <ReservationsNewClient memberOptions={memberOptions} />
}
