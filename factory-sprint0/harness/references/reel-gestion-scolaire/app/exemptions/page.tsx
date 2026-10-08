import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import ExemptionsClient from './page-client'
import { exemptionService } from '@/lib/services/exemption.service'
import { getCurrentRole } from '@/lib/auth-role'

export const dynamic = 'force-dynamic'

export default async function ExemptionsPage() {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const _role = await getCurrentRole()
  const items = _role === 'direction'
    ? await exemptionService.getAllAsAdmin()
    : await exemptionService.getAllWithRelations(userId)
  return <ExemptionsClient items={items} />
}
