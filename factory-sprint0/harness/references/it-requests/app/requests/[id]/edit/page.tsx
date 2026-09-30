import { auth } from '@clerk/nextjs/server'
import { redirect, notFound } from 'next/navigation'
import { requestService } from '@/lib/services/request.service'
import RequestEditClient from './page-client'

export const dynamic = 'force-dynamic'

export default async function RequestEditPage({ params }: { params: Promise<{ id: string }> }) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const { id } = await params
  const item = await requestService.getById(userId, id)
  if (!item) notFound()
  return <RequestEditClient item={item} />
}
