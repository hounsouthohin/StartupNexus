import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import TechniciansClient from './page-client'
import { technicianService } from '@/lib/services/technician.service'

export const dynamic = 'force-dynamic'

export default async function TechniciansPage() {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const items = await technicianService.getAllWithRelations(userId)
  return <TechniciansClient items={items} />
}
