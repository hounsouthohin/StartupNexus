import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import PaymentsClient from './page-client'
import { paymentService } from '@/lib/services/payment.service'
import { getCurrentRole } from '@/lib/auth-role'

export const dynamic = 'force-dynamic'

export default async function PaymentsPage() {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const _role = await getCurrentRole()
  const items = _role === 'admin'
    ? await paymentService.getAllAsAdmin()
    : await paymentService.getAllWithRelations(userId)
  return <PaymentsClient items={items} />
}
