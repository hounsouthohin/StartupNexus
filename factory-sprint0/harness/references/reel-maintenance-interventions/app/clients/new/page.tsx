import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import ClientsNewClient from './page-client'

export const dynamic = 'force-dynamic'

export default async function ClientsNewPage() {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  return <ClientsNewClient />
}
