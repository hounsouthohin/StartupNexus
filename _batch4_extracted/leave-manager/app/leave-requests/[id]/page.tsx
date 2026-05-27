import { auth } from '@clerk/nextjs/server'
import { redirect, notFound } from 'next/navigation'
import LeaveRequestsIdClient from './page-client'
import { leaveRequestService } from '@/lib/services/leave-request.service'

export const dynamic = 'force-dynamic'

export default async function LeaveRequestsIdPage({ params }: { params: { id: string } }) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const item = await leaveRequestService.getById(userId, params.id)
  if (!item) notFound()
  return <LeaveRequestsIdClient item={item} />
}
