import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import PaymentsNewClient from './page-client'

export const dynamic = 'force-dynamic'

export default async function PaymentsNewPage() {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  return <PaymentsNewClient />
}
