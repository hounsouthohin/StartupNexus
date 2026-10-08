import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import InternshipsClient from './page-client'
import { internshipService } from '@/lib/services/internship.service'
import { getCurrentRole } from '@/lib/auth-role'

export const dynamic = 'force-dynamic'

export default async function InternshipsPage() {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const _role = await getCurrentRole()
  const items = _role === 'direction'
    ? await internshipService.getAllAsAdmin()
    : await internshipService.getAllWithRelations(userId)
  return <InternshipsClient items={items} />
}
