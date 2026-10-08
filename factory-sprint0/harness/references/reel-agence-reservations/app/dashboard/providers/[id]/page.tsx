import { auth } from '@clerk/nextjs/server'
import { redirect, notFound } from 'next/navigation'
import DashboardProvidersIdClient from './page-client'
import { providerService } from '@/lib/services/provider.service'

export const dynamic = 'force-dynamic'

export default async function DashboardProvidersIdPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const item = await providerService.getByIdWithRelations(userId, id)
  if (!item) notFound()
  return <DashboardProvidersIdClient item={item} />
}
