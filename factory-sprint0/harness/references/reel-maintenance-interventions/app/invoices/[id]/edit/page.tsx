import { auth } from '@clerk/nextjs/server'
import { redirect, notFound } from 'next/navigation'
import { invoiceService } from '@/lib/services/invoice.service'
import { clientService } from '@/lib/services/client.service'
import { technicianService } from '@/lib/services/technician.service'
import InvoiceEditClient from './page-client'

export const dynamic = 'force-dynamic'

export default async function InvoiceEditPage({ params }: { params: Promise<{ id: string }> }) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const { id } = await params
  const item = await invoiceService.getById(userId, id)
  if (!item) notFound()
  const clientOptions = await clientService.getAll(userId)
  const technicianOptions = await technicianService.getAll(userId)
  return <InvoiceEditClient item={item} clientOptions={clientOptions} technicianOptions={technicianOptions} />
}
