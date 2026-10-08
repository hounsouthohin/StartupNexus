import { auth } from '@clerk/nextjs/server'
import { redirect, notFound } from 'next/navigation'
import DstPlanningsIdClient from './page-client'
import { dSTPlanningService } from '@/lib/services/d-s-t-planning.service'
import { getCurrentRole } from '@/lib/auth-role'

export const dynamic = 'force-dynamic'

export default async function DstPlanningsIdPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const _role = await getCurrentRole()
  const item = _role === 'direction'
    ? await dSTPlanningService.getByIdAsAdmin(id)
    : await dSTPlanningService.getById(userId, id)
  if (!item) notFound()
  return <DstPlanningsIdClient item={item} />
}
