import { auth } from '@clerk/nextjs/server'
import { redirect, notFound } from 'next/navigation'
import { timetableService } from '@/lib/services/timetable.service'
import TimetableEditClient from './page-client'

export const dynamic = 'force-dynamic'

export default async function TimetableEditPage({ params }: { params: Promise<{ id: string }> }) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const { id } = await params
  const item = await timetableService.getById(userId, id)
  if (!item) notFound()
  return <TimetableEditClient item={item} />
}
