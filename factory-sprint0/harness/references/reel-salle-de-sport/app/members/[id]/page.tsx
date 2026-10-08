import { auth } from '@clerk/nextjs/server'
import { redirect, notFound } from 'next/navigation'
import MembersIdClient from './page-client'
import { memberService } from '@/lib/services/member.service'
import { getCurrentRole } from '@/lib/auth-role'

export const dynamic = 'force-dynamic'

export default async function MembersIdPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const _role = await getCurrentRole()
  const item = _role === 'admin'
    ? await memberService.getByIdAsAdmin(id)
    : await memberService.getById(userId, id)
  if (!item) notFound()
  return <MembersIdClient item={item} />
}
