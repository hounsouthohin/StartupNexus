import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import InterventionsNewClient from './page-client'
import { machineService } from '@/lib/services/machine.service'

export const dynamic = 'force-dynamic'

export default async function InterventionsNewPage() {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const machineOptions = await machineService.getAll(userId)
  return <InterventionsNewClient machineOptions={machineOptions} />
}
