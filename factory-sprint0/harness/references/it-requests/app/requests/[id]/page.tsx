import { auth } from '@clerk/nextjs/server'
import { redirect, notFound } from 'next/navigation'
import RequestsIdClient from './page-client'
import { requestService } from '@/lib/services/request.service'
import { getCurrentRole } from '@/lib/auth-role'

export const dynamic = 'force-dynamic'

export default async function RequestsIdPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const _role = await getCurrentRole()
  const item = _role === 'admin'
    ? await requestService.getByIdAsAdmin(id)
    : await requestService.getById(userId, id)
  if (!item) notFound()
  return <RequestsIdClient item={item} />
}
