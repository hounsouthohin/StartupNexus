import { auth } from '@clerk/nextjs/server'
import { redirect, notFound } from 'next/navigation'
import { annualPlanningService } from '@/lib/services/annual-planning.service'
import AnnualPlanningEditClient from './page-client'

export const dynamic = 'force-dynamic'

export default async function AnnualPlanningEditPage({ params }: { params: Promise<{ id: string }> }) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const { id } = await params
  const item = await annualPlanningService.getById(userId, id)
  if (!item) notFound()
  return <AnnualPlanningEditClient item={item} />
}
