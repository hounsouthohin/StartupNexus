import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import SanctionsClient from './page-client'
import { sanctionService } from '@/lib/services/sanction.service'
import { getCurrentRole } from '@/lib/auth-role'

export const dynamic = 'force-dynamic'

export default async function SanctionsPage() {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const _role = await getCurrentRole()
  const items = _role === 'direction'
    ? await sanctionService.getAllAsAdmin()
    : await sanctionService.getAllWithRelations(userId)
  return <SanctionsClient items={items} />
}
