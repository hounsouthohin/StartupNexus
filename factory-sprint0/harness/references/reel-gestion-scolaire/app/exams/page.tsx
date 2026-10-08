import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import ExamsClient from './page-client'
import { examService } from '@/lib/services/exam.service'
import { getCurrentRole } from '@/lib/auth-role'

export const dynamic = 'force-dynamic'

export default async function ExamsPage() {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const _role = await getCurrentRole()
  const items = _role === 'direction'
    ? await examService.getAllAsAdmin()
    : await examService.getAllWithRelations(userId)
  return <ExamsClient items={items} />
}
