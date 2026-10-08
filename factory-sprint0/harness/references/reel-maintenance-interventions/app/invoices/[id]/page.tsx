import { auth } from '@clerk/nextjs/server'
import { redirect, notFound } from 'next/navigation'
import InvoicesIdClient from './page-client'
import { invoiceService } from '@/lib/services/invoice.service'
import { getCurrentRole } from '@/lib/auth-role'

export const dynamic = 'force-dynamic'

export default async function InvoicesIdPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const _role = await getCurrentRole()
  const item = _role === 'admin'
    ? await invoiceService.getByIdWithRelationsAsAdmin(id)
    : await invoiceService.getByIdWithRelations(userId, id)
  if (!item) notFound()
  return <InvoicesIdClient item={item} />
}
