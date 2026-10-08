import { auth } from '@clerk/nextjs/server'
import { redirect, notFound } from 'next/navigation'
import ExemptionsIdClient from './page-client'
import { exemptionService } from '@/lib/services/exemption.service'
import { getCurrentRole } from '@/lib/auth-role'

export const dynamic = 'force-dynamic'

export default async function ExemptionsIdPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const _role = await getCurrentRole()
  const item = _role === 'direction'
    ? await exemptionService.getByIdWithRelationsAsAdmin(id)
    : await exemptionService.getByIdWithRelations(userId, id)
  if (!item) notFound()
  return <ExemptionsIdClient item={item} />
}
