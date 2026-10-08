import { auth } from '@clerk/nextjs/server'
import { redirect, notFound } from 'next/navigation'
import DisciplinesIdClient from './page-client'
import { disciplineService } from '@/lib/services/discipline.service'
import { getCurrentRole } from '@/lib/auth-role'

export const dynamic = 'force-dynamic'

export default async function DisciplinesIdPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const _role = await getCurrentRole()
  const item = _role === 'direction'
    ? await disciplineService.getByIdAsAdmin(id)
    : await disciplineService.getById(userId, id)
  if (!item) notFound()
  return <DisciplinesIdClient item={item} />
}
