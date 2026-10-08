import { auth } from '@clerk/nextjs/server'
import { redirect, notFound } from 'next/navigation'
import { progressReportService } from '@/lib/services/progress-report.service'
import ProgressReportEditClient from './page-client'

export const dynamic = 'force-dynamic'

export default async function ProgressReportEditPage({ params }: { params: Promise<{ id: string }> }) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const { id } = await params
  const item = await progressReportService.getById(userId, id)
  if (!item) notFound()
  return <ProgressReportEditClient item={item} />
}
