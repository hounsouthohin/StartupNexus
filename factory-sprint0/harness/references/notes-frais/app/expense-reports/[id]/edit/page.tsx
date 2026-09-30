import { auth } from '@clerk/nextjs/server'
import { redirect, notFound } from 'next/navigation'
import { expenseReportService } from '@/lib/services/expense-report.service'
import ExpenseReportEditClient from './page-client'

export const dynamic = 'force-dynamic'

export default async function ExpenseReportEditPage({ params }: { params: Promise<{ id: string }> }) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const { id } = await params
  const item = await expenseReportService.getById(userId, id)
  if (!item) notFound()
  return <ExpenseReportEditClient item={item} />
}
