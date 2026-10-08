import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import MachinesNewClient from './page-client'
import { clientService } from '@/lib/services/client.service'

export const dynamic = 'force-dynamic'

export default async function MachinesNewPage() {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const clientOptions = await clientService.getAll(userId)
  return <MachinesNewClient clientOptions={clientOptions} />
}
