import { auth } from '@clerk/nextjs/server'
import { redirect, notFound } from 'next/navigation'
import ProgressReportsIdClient from './page-client'
import { progressReportService } from '@/lib/services/progress-report.service'
import { getCurrentRole } from '@/lib/auth-role'

export const dynamic = 'force-dynamic'

export default async function ProgressReportsIdPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const _role = await getCurrentRole()
  const item = _role === 'direction'
    ? await progressReportService.getByIdWithRelationsAsAdmin(id)
    : await progressReportService.getByIdWithRelations(userId, id)
  if (!item) notFound()
  return <ProgressReportsIdClient item={item} />
}
