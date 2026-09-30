import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import RequestsClient from './page-client'
import { requestService } from '@/lib/services/request.service'
import { getCurrentRole } from '@/lib/auth-role'

export const dynamic = 'force-dynamic'

export default async function RequestsPage() {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const _role = await getCurrentRole()
  const items = _role === 'admin'
    ? await requestService.getAllAsAdmin()
    : await requestService.getAll(userId)
  return <RequestsClient items={items} />
}
