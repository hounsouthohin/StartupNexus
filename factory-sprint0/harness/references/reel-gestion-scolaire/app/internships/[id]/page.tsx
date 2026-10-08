import { auth } from '@clerk/nextjs/server'
import { redirect, notFound } from 'next/navigation'
import InternshipsIdClient from './page-client'
import { internshipService } from '@/lib/services/internship.service'
import { getCurrentRole } from '@/lib/auth-role'

export const dynamic = 'force-dynamic'

export default async function InternshipsIdPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const _role = await getCurrentRole()
  const item = _role === 'direction'
    ? await internshipService.getByIdWithRelationsAsAdmin(id)
    : await internshipService.getByIdWithRelations(userId, id)
  if (!item) notFound()
  return <InternshipsIdClient item={item} />
}
