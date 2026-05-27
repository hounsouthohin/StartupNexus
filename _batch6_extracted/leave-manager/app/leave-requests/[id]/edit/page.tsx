import { auth } from '@clerk/nextjs/server'
import { redirect, notFound } from 'next/navigation'
import { leaveRequestService } from '@/lib/services/leave-request.service'
import LeaveRequestEditClient from './page-client'

export const dynamic = 'force-dynamic'

export default async function LeaveRequestEditPage({ params }: { params: { id: string } }) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const item = await leaveRequestService.getById(userId, params.id)
  if (!item) notFound()
  return <LeaveRequestEditClient item={item} />
}
