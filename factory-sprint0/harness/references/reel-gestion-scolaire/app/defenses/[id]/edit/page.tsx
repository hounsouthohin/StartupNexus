import { auth } from '@clerk/nextjs/server'
import { redirect, notFound } from 'next/navigation'
import { defenseService } from '@/lib/services/defense.service'
import DefenseEditClient from './page-client'

export const dynamic = 'force-dynamic'

export default async function DefenseEditPage({ params }: { params: Promise<{ id: string }> }) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const { id } = await params
  const item = await defenseService.getById(userId, id)
  if (!item) notFound()
  return <DefenseEditClient item={item} />
}
