import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import DashboardClientsClient from './page-client'
import { clientService } from '@/lib/services/client.service'
import { getCurrentRole } from '@/lib/auth-role'

export const dynamic = 'force-dynamic'

export default async function DashboardClientsPage() {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const _role = await getCurrentRole()
  const items = _role === 'admin'
    ? await clientService.getAllAsAdmin()
    : await clientService.getAllWithRelations(userId)
  return <DashboardClientsClient items={items} />
}
