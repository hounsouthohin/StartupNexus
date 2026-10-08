import { auth } from '@clerk/nextjs/server'
import { redirect, notFound } from 'next/navigation'
import TimetablesIdClient from './page-client'
import { timetableService } from '@/lib/services/timetable.service'
import { getCurrentRole } from '@/lib/auth-role'

export const dynamic = 'force-dynamic'

export default async function TimetablesIdPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const _role = await getCurrentRole()
  const item = _role === 'direction'
    ? await timetableService.getByIdAsAdmin(id)
    : await timetableService.getById(userId, id)
  if (!item) notFound()
  return <TimetablesIdClient item={item} />
}
