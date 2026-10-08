import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import DstPlanningsClient from './page-client'
import { dSTPlanningService } from '@/lib/services/d-s-t-planning.service'
import { getCurrentRole } from '@/lib/auth-role'

export const dynamic = 'force-dynamic'

export default async function DstPlanningsPage() {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const _role = await getCurrentRole()
  const items = _role === 'direction'
    ? await dSTPlanningService.getAllAsAdmin()
    : await dSTPlanningService.getAll(userId)
  return <DstPlanningsClient items={items} />
}
