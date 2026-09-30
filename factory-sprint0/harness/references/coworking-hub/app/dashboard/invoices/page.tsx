import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import DashboardInvoicesClient from './page-client'
import { invoiceService } from '@/lib/services/invoice.service'
import { getCurrentRole } from '@/lib/auth-role'

export const dynamic = 'force-dynamic'

export default async function DashboardInvoicesPage() {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const _role = await getCurrentRole()
  const items = _role === 'admin'
    ? await invoiceService.getAllAsAdmin()
    : await invoiceService.getAllWithRelations(userId)
  return <DashboardInvoicesClient items={items} />
}
