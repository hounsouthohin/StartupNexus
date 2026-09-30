import { auth } from '@clerk/nextjs/server'
import { redirect, notFound } from 'next/navigation'
import DashboardRepairsIdClient from './page-client'
import { repairService } from '@/lib/services/repair.service'
import { getCurrentRole } from '@/lib/auth-role'

export const dynamic = 'force-dynamic'

export default async function DashboardRepairsIdPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const _role = await getCurrentRole()
  const item = _role === 'owner'
    ? await repairService.getByIdWithRelationsAsAdmin(id)
    : await repairService.getByIdWithRelations(userId, id)
  if (!item) notFound()
  return <DashboardRepairsIdClient item={item} />
}
