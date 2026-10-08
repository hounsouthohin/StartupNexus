import { auth } from '@clerk/nextjs/server'
import { redirect, notFound } from 'next/navigation'
import SanctionsIdClient from './page-client'
import { sanctionService } from '@/lib/services/sanction.service'
import { getCurrentRole } from '@/lib/auth-role'

export const dynamic = 'force-dynamic'

export default async function SanctionsIdPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const _role = await getCurrentRole()
  const item = _role === 'direction'
    ? await sanctionService.getByIdWithRelationsAsAdmin(id)
    : await sanctionService.getByIdWithRelations(userId, id)
  if (!item) notFound()
  return <SanctionsIdClient item={item} />
}
