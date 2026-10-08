import { auth } from '@clerk/nextjs/server'
import { redirect, notFound } from 'next/navigation'
import { machineService } from '@/lib/services/machine.service'
import { clientService } from '@/lib/services/client.service'
import MachineEditClient from './page-client'

export const dynamic = 'force-dynamic'

export default async function MachineEditPage({ params }: { params: Promise<{ id: string }> }) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const { id } = await params
  const item = await machineService.getById(userId, id)
  if (!item) notFound()
  const clientOptions = await clientService.getAll(userId)
  return <MachineEditClient item={item} clientOptions={clientOptions} />
}
