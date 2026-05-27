import { auth } from '@clerk/nextjs/server'
import { redirect, notFound } from 'next/navigation'
import { expenseService } from '@/lib/services/expense.service'
import { categoryService } from '@/lib/services/category.service'
import ExpenseEditClient from './page-client'

export const dynamic = 'force-dynamic'

export default async function ExpenseEditPage({ params }: { params: { id: string } }) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const item = await expenseService.getById(userId, params.id)
  if (!item) notFound()
  const categoryOptions = await categoryService.getAll(userId)
  return <ExpenseEditClient item={item} categoryOptions={categoryOptions} />
}
