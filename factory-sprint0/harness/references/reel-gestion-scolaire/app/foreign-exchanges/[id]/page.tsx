import { auth } from '@clerk/nextjs/server'
import { redirect, notFound } from 'next/navigation'
import ForeignExchangesIdClient from './page-client'
import { foreignExchangeService } from '@/lib/services/foreign-exchange.service'
import { getCurrentRole } from '@/lib/auth-role'

export const dynamic = 'force-dynamic'

export default async function ForeignExchangesIdPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const _role = await getCurrentRole()
  const item = _role === 'direction'
    ? await foreignExchangeService.getByIdWithRelationsAsAdmin(id)
    : await foreignExchangeService.getByIdWithRelations(userId, id)
  if (!item) notFound()
  return <ForeignExchangesIdClient item={item} />
}
