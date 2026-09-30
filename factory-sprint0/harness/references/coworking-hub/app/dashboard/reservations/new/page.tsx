import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import DashboardReservationsNewClient from './page-client'
import { getCurrentRole } from '@/lib/auth-role'
import { spaceService } from '@/lib/services/space.service'
import { memberService } from '@/lib/services/member.service'

export const dynamic = 'force-dynamic'

export default async function DashboardReservationsNewPage() {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  if ((await getCurrentRole()) === 'admin') redirect('/dashboard/reservations')
  const spaceOptions = await spaceService.getAll(userId)
  const memberOptions = await memberService.getAll(userId)
  return <DashboardReservationsNewClient spaceOptions={spaceOptions} memberOptions={memberOptions} />
}
