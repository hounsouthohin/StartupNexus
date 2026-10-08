import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import DigitalResourcesClient from './page-client'
import { digitalResourceService } from '@/lib/services/digital-resource.service'
import { getCurrentRole } from '@/lib/auth-role'

export const dynamic = 'force-dynamic'

export default async function DigitalResourcesPage() {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const _role = await getCurrentRole()
  const items = _role === 'direction'
    ? await digitalResourceService.getAllAsAdmin()
    : await digitalResourceService.getAll(userId)
  return <DigitalResourcesClient items={items} />
}
