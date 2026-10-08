import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import InterventionsNewClient from './page-client'
import { getCurrentRole } from '@/lib/auth-role'
import { clientService } from '@/lib/services/client.service'
import { technicianService } from '@/lib/services/technician.service'

export const dynamic = 'force-dynamic'

export default async function InterventionsNewPage() {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  if ((await getCurrentRole()) !== 'admin') redirect('/interventions')
  const clientOptions = await clientService.getAll(userId)
  const technicianOptions = await technicianService.getAll(userId)
  return <InterventionsNewClient clientOptions={clientOptions} technicianOptions={technicianOptions} />
}
