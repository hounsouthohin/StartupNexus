import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import LeaveRequestsNewClient from './page-client'

export const dynamic = 'force-dynamic'

export default async function LeaveRequestsNewPage() {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  return <LeaveRequestsNewClient />
}
