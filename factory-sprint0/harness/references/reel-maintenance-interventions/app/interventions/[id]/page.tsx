import { auth } from '@clerk/nextjs/server'
import { redirect, notFound } from 'next/navigation'
import InterventionsIdClient from './page-client'
import { interventionService } from '@/lib/services/intervention.service'
import { getCurrentRole } from '@/lib/auth-role'

export const dynamic = 'force-dynamic'

export default async function InterventionsIdPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const _role = await getCurrentRole()
  const item = _role === 'admin'
    ? await interventionService.getByIdWithRelationsAsAdmin(id)
    : await interventionService.getByIdWithRelations(userId, id)
  if (!item) notFound()
  return <InterventionsIdClient item={item} />
}
