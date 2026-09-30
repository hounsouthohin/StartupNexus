import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import DashboardCategoriesNewClient from './page-client'

export const dynamic = 'force-dynamic'

export default async function DashboardCategoriesNewPage() {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  return <DashboardCategoriesNewClient />
}
