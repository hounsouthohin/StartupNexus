import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import DashboardRecipesNewClient from './page-client'
import { categoryService } from '@/lib/services/category.service'

export const dynamic = 'force-dynamic'

export default async function DashboardRecipesNewPage() {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const categoryOptions = await categoryService.getAll(userId)
  return <DashboardRecipesNewClient categoryOptions={categoryOptions} />
}
