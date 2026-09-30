import { auth } from '@clerk/nextjs/server'
import { redirect, notFound } from 'next/navigation'
import { workshopService } from '@/lib/services/workshop.service'
import { domainService } from '@/lib/services/domain.service'
import WorkshopEditClient from './page-client'

export const dynamic = 'force-dynamic'

export default async function WorkshopEditPage({ params }: { params: Promise<{ id: string }> }) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const { id } = await params
  const item = await workshopService.getByIdWithRelations(userId, id)
  if (!item) notFound()
  const domainOptions = await domainService.getAll(userId)
  return <WorkshopEditClient item={item} domainOptions={domainOptions} />
}
