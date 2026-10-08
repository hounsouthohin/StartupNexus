import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import SanctionsNewClient from './page-client'

export const dynamic = 'force-dynamic'

export default async function SanctionsNewPage() {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  return <SanctionsNewClient />
}
