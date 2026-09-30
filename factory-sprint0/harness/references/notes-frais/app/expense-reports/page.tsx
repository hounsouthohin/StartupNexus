import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import ExpenseReportsClient from './page-client'
import { expenseReportService } from '@/lib/services/expense-report.service'

export const dynamic = 'force-dynamic'

export default async function ExpenseReportsPage() {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const items = await expenseReportService.getAll(userId)
  return <ExpenseReportsClient items={items} />
}
