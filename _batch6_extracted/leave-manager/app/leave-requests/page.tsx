import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import LeaveRequestsClient from './page-client'
import { leaveRequestService } from '@/lib/services/leave-request.service'

export const dynamic = 'force-dynamic'

export default async function LeaveRequestsPage() {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const items = await leaveRequestService.getAll(userId)
  return <LeaveRequestsClient items={items} />
}
