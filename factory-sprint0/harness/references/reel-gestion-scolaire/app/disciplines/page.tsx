import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import DisciplinesClient from './page-client'
import { disciplineService } from '@/lib/services/discipline.service'
import { getCurrentRole } from '@/lib/auth-role'

export const dynamic = 'force-dynamic'

export default async function DisciplinesPage() {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const _role = await getCurrentRole()
  const items = _role === 'direction'
    ? await disciplineService.getAllAsAdmin()
    : await disciplineService.getAll(userId)
  return <DisciplinesClient items={items} />
}
