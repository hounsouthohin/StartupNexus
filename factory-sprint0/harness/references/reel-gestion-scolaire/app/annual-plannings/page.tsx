import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import AnnualPlanningsClient from './page-client'
import { annualPlanningService } from '@/lib/services/annual-planning.service'
import { getCurrentRole } from '@/lib/auth-role'

export const dynamic = 'force-dynamic'

export default async function AnnualPlanningsPage() {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const _role = await getCurrentRole()
  const items = _role === 'direction'
    ? await annualPlanningService.getAllAsAdmin()
    : await annualPlanningService.getAll(userId)
  return <AnnualPlanningsClient items={items} />
}
