import { auth } from '@clerk/nextjs/server'
import { redirect, notFound } from 'next/navigation'
import AnnualPlanningsIdClient from './page-client'
import { annualPlanningService } from '@/lib/services/annual-planning.service'
import { getCurrentRole } from '@/lib/auth-role'

export const dynamic = 'force-dynamic'

export default async function AnnualPlanningsIdPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const _role = await getCurrentRole()
  const item = _role === 'direction'
    ? await annualPlanningService.getByIdAsAdmin(id)
    : await annualPlanningService.getById(userId, id)
  if (!item) notFound()
  return <AnnualPlanningsIdClient item={item} />
}
