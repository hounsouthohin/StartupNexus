import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import InternshipsNewClient from './page-client'

export const dynamic = 'force-dynamic'

export default async function InternshipsNewPage() {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  return <InternshipsNewClient />
}
