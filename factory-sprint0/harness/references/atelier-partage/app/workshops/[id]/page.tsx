import { notFound } from 'next/navigation'
import WorkshopsIdClient from './page-client'
import { workshopService } from '@/lib/services/workshop.service'

export const dynamic = 'force-dynamic'

export default async function WorkshopsIdPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params
  const item = await workshopService.getPublicByIdWithRelations(id)
  if (!item) notFound()
  return <WorkshopsIdClient item={item} />
}
