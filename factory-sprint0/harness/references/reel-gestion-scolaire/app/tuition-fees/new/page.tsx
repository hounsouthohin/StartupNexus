import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import TuitionFeesNewClient from './page-client'

export const dynamic = 'force-dynamic'

export default async function TuitionFeesNewPage() {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  return <TuitionFeesNewClient />
}
