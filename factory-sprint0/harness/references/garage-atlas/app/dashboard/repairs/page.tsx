import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import DashboardRepairsClient from './page-client'
import { repairService } from '@/lib/services/repair.service'
import { getCurrentRole } from '@/lib/auth-role'

export const dynamic = 'force-dynamic'

export default async function DashboardRepairsPage() {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const _role = await getCurrentRole()
  const items = _role === 'owner'
    ? await repairService.getAllAsAdmin()
    : await repairService.getAllWithRelations(userId)
  return <DashboardRepairsClient items={items} />
}
