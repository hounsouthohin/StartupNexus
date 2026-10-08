import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import DashboardManagersNewClient from './page-client'
import { providerService } from '@/lib/services/provider.service'

export const dynamic = 'force-dynamic'

export default async function DashboardManagersNewPage() {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const providerOptions = await providerService.getAll(userId)
  return <DashboardManagersNewClient providerOptions={providerOptions} />
}
