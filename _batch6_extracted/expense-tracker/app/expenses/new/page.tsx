import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import ExpensesNewClient from './page-client'
import { categoryService } from '@/lib/services/category.service'

export const dynamic = 'force-dynamic'

export default async function ExpensesNewPage() {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const categoryOptions = await categoryService.getAll(userId)
  return <ExpensesNewClient categoryOptions={categoryOptions} />
}
