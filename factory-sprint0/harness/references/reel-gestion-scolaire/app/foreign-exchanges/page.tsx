import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import ForeignExchangesClient from './page-client'
import { foreignExchangeService } from '@/lib/services/foreign-exchange.service'
import { getCurrentRole } from '@/lib/auth-role'

export const dynamic = 'force-dynamic'

export default async function ForeignExchangesPage() {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const _role = await getCurrentRole()
  const items = _role === 'direction'
    ? await foreignExchangeService.getAllAsAdmin()
    : await foreignExchangeService.getAllWithRelations(userId)
  return <ForeignExchangesClient items={items} />
}
