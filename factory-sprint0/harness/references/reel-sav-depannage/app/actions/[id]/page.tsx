import { auth } from '@clerk/nextjs/server'
import { redirect, notFound } from 'next/navigation'
import ActionsIdClient from './page-client'
import { actionService } from '@/lib/services/action.service'

export const dynamic = 'force-dynamic'

export default async function ActionsIdPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const item = await actionService.getByIdWithRelations(userId, id)
  if (!item) notFound()
  return <ActionsIdClient item={item} />
}
