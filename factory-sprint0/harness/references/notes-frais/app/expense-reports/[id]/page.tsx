import { auth } from '@clerk/nextjs/server'
import { redirect, notFound } from 'next/navigation'
import ExpenseReportsIdClient from './page-client'
import { expenseReportService } from '@/lib/services/expense-report.service'

export const dynamic = 'force-dynamic'

export default async function ExpenseReportsIdPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const item = await expenseReportService.getById(userId, id)
  if (!item) notFound()
  return <ExpenseReportsIdClient item={item} />
}
