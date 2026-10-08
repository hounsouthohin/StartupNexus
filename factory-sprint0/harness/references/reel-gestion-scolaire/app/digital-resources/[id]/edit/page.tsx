import { auth } from '@clerk/nextjs/server'
import { redirect, notFound } from 'next/navigation'
import { digitalResourceService } from '@/lib/services/digital-resource.service'
import DigitalResourceEditClient from './page-client'

export const dynamic = 'force-dynamic'

export default async function DigitalResourceEditPage({ params }: { params: Promise<{ id: string }> }) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const { id } = await params
  const item = await digitalResourceService.getById(userId, id)
  if (!item) notFound()
  return <DigitalResourceEditClient item={item} />
}
