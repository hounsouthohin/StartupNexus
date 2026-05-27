import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import ExpensesClient from './page-client'
import { expenseService } from '@/lib/services/expense.service'

export const dynamic = 'force-dynamic'

export default async function ExpensesPage() {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const items = await expenseService.getAllWithRelations(userId)
  return <ExpensesClient items={items} />
}
