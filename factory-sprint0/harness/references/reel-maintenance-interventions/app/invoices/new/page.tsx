import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import InvoicesNewClient from './page-client'
import { clientService } from '@/lib/services/client.service'
import { technicianService } from '@/lib/services/technician.service'

export const dynamic = 'force-dynamic'

export default async function InvoicesNewPage() {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const clientOptions = await clientService.getAll(userId)
  const technicianOptions = await technicianService.getAll(userId)
  return <InvoicesNewClient clientOptions={clientOptions} technicianOptions={technicianOptions} />
}
