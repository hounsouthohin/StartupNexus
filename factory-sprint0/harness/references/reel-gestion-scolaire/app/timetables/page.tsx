import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import TimetablesClient from './page-client'
import { timetableService } from '@/lib/services/timetable.service'
import { getCurrentRole } from '@/lib/auth-role'

export const dynamic = 'force-dynamic'

export default async function TimetablesPage() {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const _role = await getCurrentRole()
  const items = _role === 'direction'
    ? await timetableService.getAllAsAdmin()
    : await timetableService.getAll(userId)
  return <TimetablesClient items={items} />
}
