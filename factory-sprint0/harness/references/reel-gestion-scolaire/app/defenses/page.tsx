import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import DefensesClient from './page-client'
import { defenseService } from '@/lib/services/defense.service'
import { getCurrentRole } from '@/lib/auth-role'

export const dynamic = 'force-dynamic'

export default async function DefensesPage() {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const _role = await getCurrentRole()
  const items = _role === 'direction'
    ? await defenseService.getAllAsAdmin()
    : await defenseService.getAllWithRelations(userId)
  return <DefensesClient items={items} />
}
