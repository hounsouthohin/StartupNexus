import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import MembersClient from './page-client'
import { memberService } from '@/lib/services/member.service'
import { getCurrentRole } from '@/lib/auth-role'

export const dynamic = 'force-dynamic'

export default async function MembersPage() {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const _role = await getCurrentRole()
  const items = _role === 'admin'
    ? await memberService.getAllAsAdmin()
    : await memberService.getAll(userId)
  return <MembersClient items={items} />
}
