import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import RequestsNewClient from './page-client'
import { getCurrentRole } from '@/lib/auth-role'

export const dynamic = 'force-dynamic'

export default async function RequestsNewPage() {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  if ((await getCurrentRole()) === 'admin') redirect('/requests')
  return <RequestsNewClient />
}
