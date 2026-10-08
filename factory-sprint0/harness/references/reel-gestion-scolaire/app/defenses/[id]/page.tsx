import { auth } from '@clerk/nextjs/server'
import { redirect, notFound } from 'next/navigation'
import DefensesIdClient from './page-client'
import { defenseService } from '@/lib/services/defense.service'
import { getCurrentRole } from '@/lib/auth-role'

export const dynamic = 'force-dynamic'

export default async function DefensesIdPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const _role = await getCurrentRole()
  const item = _role === 'direction'
    ? await defenseService.getByIdWithRelationsAsAdmin(id)
    : await defenseService.getByIdWithRelations(userId, id)
  if (!item) notFound()
  return <DefensesIdClient item={item} />
}
