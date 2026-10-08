import { auth } from '@clerk/nextjs/server'
import { redirect, notFound } from 'next/navigation'
import DashboardManagersIdClient from './page-client'
import { managerService } from '@/lib/services/manager.service'

export const dynamic = 'force-dynamic'

export default async function DashboardManagersIdPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const item = await managerService.getByIdWithRelations(userId, id)
  if (!item) notFound()
  return <DashboardManagersIdClient item={item} />
}
