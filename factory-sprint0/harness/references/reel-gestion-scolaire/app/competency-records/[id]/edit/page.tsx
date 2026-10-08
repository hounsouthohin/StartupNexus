import { auth } from '@clerk/nextjs/server'
import { redirect, notFound } from 'next/navigation'
import { competencyRecordService } from '@/lib/services/competency-record.service'
import CompetencyRecordEditClient from './page-client'

export const dynamic = 'force-dynamic'

export default async function CompetencyRecordEditPage({ params }: { params: Promise<{ id: string }> }) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const { id } = await params
  const item = await competencyRecordService.getById(userId, id)
  if (!item) notFound()
  return <CompetencyRecordEditClient item={item} />
}
