import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import ExpenseReportsNewClient from './page-client'

export const dynamic = 'force-dynamic'

export default async function ExpenseReportsNewPage() {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  return <ExpenseReportsNewClient />
}
