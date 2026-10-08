import { auth } from '@clerk/nextjs/server'
import { redirect, notFound } from 'next/navigation'
import CircularsIdClient from './page-client'
import { circularService } from '@/lib/services/circular.service'
import { getCurrentRole } from '@/lib/auth-role'

export const dynamic = 'force-dynamic'

export default async function CircularsIdPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const _role = await getCurrentRole()
  const item = _role === 'direction'
    ? await circularService.getByIdAsAdmin(id)
    : await circularService.getById(userId, id)
  if (!item) notFound()
  return <CircularsIdClient item={item} />
}
