import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import ActionsClient from './page-client'
import { actionService } from '@/lib/services/action.service'

export const dynamic = 'force-dynamic'

export default async function ActionsPage() {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const items = await actionService.getAllWithRelations(userId)
  return <ActionsClient items={items} />
}
