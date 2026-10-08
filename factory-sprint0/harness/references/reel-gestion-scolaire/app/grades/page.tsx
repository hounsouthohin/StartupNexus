import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import GradesClient from './page-client'
import { gradeService } from '@/lib/services/grade.service'
import { getCurrentRole } from '@/lib/auth-role'

export const dynamic = 'force-dynamic'

export default async function GradesPage() {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const _role = await getCurrentRole()
  const items = _role === 'direction'
    ? await gradeService.getAllAsAdmin()
    : await gradeService.getAllWithRelations(userId)
  return <GradesClient items={items} />
}
