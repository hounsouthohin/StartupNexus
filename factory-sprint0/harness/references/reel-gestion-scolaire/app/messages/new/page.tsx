import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import MessagesNewClient from './page-client'

export const dynamic = 'force-dynamic'

export default async function MessagesNewPage() {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  return <MessagesNewClient />
}
