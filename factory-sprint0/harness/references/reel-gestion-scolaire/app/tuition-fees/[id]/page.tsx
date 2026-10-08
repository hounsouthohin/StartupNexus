import { auth } from '@clerk/nextjs/server'
import { redirect, notFound } from 'next/navigation'
import TuitionFeesIdClient from './page-client'
import { tuitionFeeService } from '@/lib/services/tuition-fee.service'
import { getCurrentRole } from '@/lib/auth-role'

export const dynamic = 'force-dynamic'

export default async function TuitionFeesIdPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const _role = await getCurrentRole()
  const item = _role === 'direction'
    ? await tuitionFeeService.getByIdWithRelationsAsAdmin(id)
    : await tuitionFeeService.getByIdWithRelations(userId, id)
  if (!item) notFound()
  return <TuitionFeesIdClient item={item} />
}
