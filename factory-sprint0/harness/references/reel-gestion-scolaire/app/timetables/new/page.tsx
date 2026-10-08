import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import TimetablesNewClient from './page-client'

export const dynamic = 'force-dynamic'

export default async function TimetablesNewPage() {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  return <TimetablesNewClient />
}
