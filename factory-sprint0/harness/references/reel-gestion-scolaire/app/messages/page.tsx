import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import MessagesClient from './page-client'
import { messageService } from '@/lib/services/message.service'
import { getCurrentRole } from '@/lib/auth-role'

export const dynamic = 'force-dynamic'

export default async function MessagesPage() {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const _role = await getCurrentRole()
  const items = _role === 'direction'
    ? await messageService.getAllAsAdmin()
    : await messageService.getAll(userId)
  return <MessagesClient items={items} />
}
