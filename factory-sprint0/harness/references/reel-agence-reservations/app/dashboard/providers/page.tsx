import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import DashboardProvidersClient from './page-client'
import { providerService } from '@/lib/services/provider.service'

export const dynamic = 'force-dynamic'

export default async function DashboardProvidersPage() {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const items = await providerService.getAllWithRelations(userId)
  return <DashboardProvidersClient items={items} />
}
