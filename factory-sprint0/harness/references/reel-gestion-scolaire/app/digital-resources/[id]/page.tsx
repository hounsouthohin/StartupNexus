import { auth } from '@clerk/nextjs/server'
import { redirect, notFound } from 'next/navigation'
import DigitalResourcesIdClient from './page-client'
import { digitalResourceService } from '@/lib/services/digital-resource.service'
import { getCurrentRole } from '@/lib/auth-role'

export const dynamic = 'force-dynamic'

export default async function DigitalResourcesIdPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const _role = await getCurrentRole()
  const item = _role === 'direction'
    ? await digitalResourceService.getByIdAsAdmin(id)
    : await digitalResourceService.getById(userId, id)
  if (!item) notFound()
  return <DigitalResourcesIdClient item={item} />
}
