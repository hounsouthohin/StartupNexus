import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import MachinesClient from './page-client'
import { machineService } from '@/lib/services/machine.service'

export const dynamic = 'force-dynamic'

export default async function MachinesPage() {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const items = await machineService.getAllWithRelations(userId)
  return <MachinesClient items={items} />
}
