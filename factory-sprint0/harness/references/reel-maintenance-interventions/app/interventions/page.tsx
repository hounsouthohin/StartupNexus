import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import InterventionsClient from './page-client'
import { interventionService } from '@/lib/services/intervention.service'
import { getCurrentRole } from '@/lib/auth-role'

export const dynamic = 'force-dynamic'

export default async function InterventionsPage() {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const _role = await getCurrentRole()
  const items = _role === 'admin'
    ? await interventionService.getAllAsAdmin()
    : await interventionService.getAllWithRelations(userId)
  return <InterventionsClient items={items} />
}
