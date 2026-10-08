import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import DefensesNewClient from './page-client'

export const dynamic = 'force-dynamic'

export default async function DefensesNewPage() {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  return <DefensesNewClient />
}
