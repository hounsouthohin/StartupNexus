import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import TechniciansNewClient from './page-client'

export const dynamic = 'force-dynamic'

export default async function TechniciansNewPage() {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  return <TechniciansNewClient />
}
