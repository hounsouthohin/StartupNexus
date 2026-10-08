import { auth } from '@clerk/nextjs/server'
import { redirect, notFound } from 'next/navigation'
import { managerService } from '@/lib/services/manager.service'
import { providerService } from '@/lib/services/provider.service'
import ManagerEditClient from './page-client'

export const dynamic = 'force-dynamic'

export default async function ManagerEditPage({ params }: { params: Promise<{ id: string }> }) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const { id } = await params
  const item = await managerService.getByIdWithRelations(userId, id)
  if (!item) notFound()
  const providerOptions = await providerService.getAll(userId)
  return <ManagerEditClient item={item} providerOptions={providerOptions} />
}
