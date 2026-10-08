import { auth } from '@clerk/nextjs/server'
import { redirect, notFound } from 'next/navigation'
import DashboardAlertsIdClient from './page-client'
import { alertService } from '@/lib/services/alert.service'

export const dynamic = 'force-dynamic'

export default async function DashboardAlertsIdPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const item = await alertService.getByIdWithRelations(userId, id)
  if (!item) notFound()
  return <DashboardAlertsIdClient item={item} />
}
