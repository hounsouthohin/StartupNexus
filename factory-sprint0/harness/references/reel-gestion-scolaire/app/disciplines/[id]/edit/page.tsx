import { auth } from '@clerk/nextjs/server'
import { redirect, notFound } from 'next/navigation'
import { disciplineService } from '@/lib/services/discipline.service'
import DisciplineEditClient from './page-client'

export const dynamic = 'force-dynamic'

export default async function DisciplineEditPage({ params }: { params: Promise<{ id: string }> }) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const { id } = await params
  const item = await disciplineService.getById(userId, id)
  if (!item) notFound()
  return <DisciplineEditClient item={item} />
}
