import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import CompetencyRecordsNewClient from './page-client'

export const dynamic = 'force-dynamic'

export default async function CompetencyRecordsNewPage() {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  return <CompetencyRecordsNewClient />
}
