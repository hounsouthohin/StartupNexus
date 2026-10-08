import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import SharedAgendasNewClient from './page-client'

export const dynamic = 'force-dynamic'

export default async function SharedAgendasNewPage() {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  return <SharedAgendasNewClient />
}
