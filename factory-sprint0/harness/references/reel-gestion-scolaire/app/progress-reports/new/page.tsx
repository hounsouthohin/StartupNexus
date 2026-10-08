import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import ProgressReportsNewClient from './page-client'

export const dynamic = 'force-dynamic'

export default async function ProgressReportsNewPage() {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  return <ProgressReportsNewClient />
}
