import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import DashboardCategoriesClient from './page-client'
import { categoryService } from '@/lib/services/category.service'

export const dynamic = 'force-dynamic'

export default async function DashboardCategoriesPage() {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const items = await categoryService.getAllWithRelations(userId)
  return <DashboardCategoriesClient items={items} />
}
