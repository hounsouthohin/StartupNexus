import { auth } from '@clerk/nextjs/server'
import { redirect, notFound } from 'next/navigation'
import MessagesIdClient from './page-client'
import { messageService } from '@/lib/services/message.service'
import { getCurrentRole } from '@/lib/auth-role'

export const dynamic = 'force-dynamic'

export default async function MessagesIdPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const _role = await getCurrentRole()
  const item = _role === 'direction'
    ? await messageService.getByIdAsAdmin(id)
    : await messageService.getById(userId, id)
  if (!item) notFound()
  return <MessagesIdClient item={item} />
}
