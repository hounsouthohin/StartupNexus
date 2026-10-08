import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import ExemptionsNewClient from './page-client'

export const dynamic = 'force-dynamic'

export default async function ExemptionsNewPage() {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  return <ExemptionsNewClient />
}
