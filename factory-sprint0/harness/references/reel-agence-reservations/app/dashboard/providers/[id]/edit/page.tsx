import { auth } from '@clerk/nextjs/server'
import { redirect, notFound } from 'next/navigation'
import { providerService } from '@/lib/services/provider.service'
import { managerService } from '@/lib/services/manager.service'
import ProviderEditClient from './page-client'

export const dynamic = 'force-dynamic'

export default async function ProviderEditPage({ params }: { params: Promise<{ id: string }> }) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const { id } = await params
  const item = await providerService.getByIdWithRelations(userId, id)
  if (!item) notFound()
  const managerOptions = await managerService.getAll(userId)
  return <ProviderEditClient item={item} managerOptions={managerOptions} />
}
