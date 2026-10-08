import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import AbsencesNewClient from './page-client'

export const dynamic = 'force-dynamic'

export default async function AbsencesNewPage() {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  return <AbsencesNewClient />
}
