import { auth } from '@clerk/nextjs/server'
import { redirect, notFound } from 'next/navigation'
import { messageService } from '@/lib/services/message.service'
import MessageEditClient from './page-client'

export const dynamic = 'force-dynamic'

export default async function MessageEditPage({ params }: { params: Promise<{ id: string }> }) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const { id } = await params
  const item = await messageService.getById(userId, id)
  if (!item) notFound()
  return <MessageEditClient item={item} />
}
