import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import ForeignExchangesNewClient from './page-client'

export const dynamic = 'force-dynamic'

export default async function ForeignExchangesNewPage() {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  return <ForeignExchangesNewClient />
}
