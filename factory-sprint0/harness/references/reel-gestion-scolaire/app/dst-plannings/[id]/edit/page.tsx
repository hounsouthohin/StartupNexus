import { auth } from '@clerk/nextjs/server'
import { redirect, notFound } from 'next/navigation'
import { dSTPlanningService } from '@/lib/services/d-s-t-planning.service'
import DSTPlanningEditClient from './page-client'

export const dynamic = 'force-dynamic'

export default async function DSTPlanningEditPage({ params }: { params: Promise<{ id: string }> }) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const { id } = await params
  const item = await dSTPlanningService.getById(userId, id)
  if (!item) notFound()
  return <DSTPlanningEditClient item={item} />
}
