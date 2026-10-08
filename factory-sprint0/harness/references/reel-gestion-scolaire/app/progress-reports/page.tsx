import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import ProgressReportsClient from './page-client'
import { progressReportService } from '@/lib/services/progress-report.service'
import { getCurrentRole } from '@/lib/auth-role'

export const dynamic = 'force-dynamic'

export default async function ProgressReportsPage() {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const _role = await getCurrentRole()
  const items = _role === 'direction'
    ? await progressReportService.getAllAsAdmin()
    : await progressReportService.getAllWithRelations(userId)
  return <ProgressReportsClient items={items} />
}
