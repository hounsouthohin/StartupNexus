import { auth } from '@clerk/nextjs/server'
import { redirect, notFound } from 'next/navigation'
import PaymentsIdClient from './page-client'
import { paymentService } from '@/lib/services/payment.service'
import { getCurrentRole } from '@/lib/auth-role'

export const dynamic = 'force-dynamic'

export default async function PaymentsIdPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const _role = await getCurrentRole()
  const item = _role === 'admin'
    ? await paymentService.getByIdWithRelationsAsAdmin(id)
    : await paymentService.getByIdWithRelations(userId, id)
  if (!item) notFound()
  return <PaymentsIdClient item={item} />
}
