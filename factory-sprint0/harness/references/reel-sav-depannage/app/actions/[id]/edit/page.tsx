import { auth } from '@clerk/nextjs/server'
import { redirect, notFound } from 'next/navigation'
import { actionService } from '@/lib/services/action.service'
import { interventionService } from '@/lib/services/intervention.service'
import ActionEditClient from './page-client'

export const dynamic = 'force-dynamic'

export default async function ActionEditPage({ params }: { params: Promise<{ id: string }> }) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const { id } = await params
  const item = await actionService.getById(userId, id)
  if (!item) notFound()
  const interventionOptions = await interventionService.getAll(userId)
  return <ActionEditClient item={item} interventionOptions={interventionOptions} />
}
