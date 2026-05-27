import { auth } from '@clerk/nextjs/server'
import { redirect, notFound } from 'next/navigation'
import ExpensesIdClient from './page-client'
import { expenseService } from '@/lib/services/expense.service'

export const dynamic = 'force-dynamic'

export default async function ExpensesIdPage({ params }: { params: { id: string } }) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const item = await expenseService.getByIdWithRelations(userId, params.id)
  if (!item) notFound()
  return <ExpensesIdClient item={item} />
}
