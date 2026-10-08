import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import CircularsClient from './page-client'
import { circularService } from '@/lib/services/circular.service'
import { getCurrentRole } from '@/lib/auth-role'

export const dynamic = 'force-dynamic'

export default async function CircularsPage() {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const _role = await getCurrentRole()
  const items = _role === 'direction'
    ? await circularService.getAllAsAdmin()
    : await circularService.getAll(userId)
  return <CircularsClient items={items} />
}
