import { notFound } from 'next/navigation'
import SpacesIdClient from './page-client'
import { spaceService } from '@/lib/services/space.service'

export const dynamic = 'force-dynamic'

export default async function SpacesIdPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params
  const item = await spaceService.getPublicById(id)
  if (!item) notFound()
  return <SpacesIdClient item={item} />
}
