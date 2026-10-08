import { auth } from '@clerk/nextjs/server'
import { redirect, notFound } from 'next/navigation'
import MachinesIdClient from './page-client'
import { machineService } from '@/lib/services/machine.service'

export const dynamic = 'force-dynamic'

export default async function MachinesIdPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const item = await machineService.getByIdWithRelations(userId, id)
  if (!item) notFound()
  return <MachinesIdClient item={item} />
}
