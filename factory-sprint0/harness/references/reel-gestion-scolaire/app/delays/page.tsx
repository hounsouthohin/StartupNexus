import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import DelaysClient from './page-client'
import { delayService } from '@/lib/services/delay.service'
import { getCurrentRole } from '@/lib/auth-role'

export const dynamic = 'force-dynamic'

export default async function DelaysPage() {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const _role = await getCurrentRole()
  const items = _role === 'direction'
    ? await delayService.getAllAsAdmin()
    : await delayService.getAllWithRelations(userId)
  return <DelaysClient items={items} />
}
