import { auth } from '@clerk/nextjs/server'
import { redirect, notFound } from 'next/navigation'
import DelaysIdClient from './page-client'
import { delayService } from '@/lib/services/delay.service'
import { getCurrentRole } from '@/lib/auth-role'

export const dynamic = 'force-dynamic'

export default async function DelaysIdPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const _role = await getCurrentRole()
  const item = _role === 'direction'
    ? await delayService.getByIdWithRelationsAsAdmin(id)
    : await delayService.getByIdWithRelations(userId, id)
  if (!item) notFound()
  return <DelaysIdClient item={item} />
}
