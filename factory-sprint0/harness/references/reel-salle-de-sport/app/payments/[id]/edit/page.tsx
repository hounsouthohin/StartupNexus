import { auth } from '@clerk/nextjs/server'
import { redirect, notFound } from 'next/navigation'
import { paymentService } from '@/lib/services/payment.service'
import PaymentEditClient from './page-client'

export const dynamic = 'force-dynamic'

export default async function PaymentEditPage({ params }: { params: Promise<{ id: string }> }) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const { id } = await params
  const item = await paymentService.getById(userId, id)
  if (!item) notFound()
  return <PaymentEditClient item={item} />
}
