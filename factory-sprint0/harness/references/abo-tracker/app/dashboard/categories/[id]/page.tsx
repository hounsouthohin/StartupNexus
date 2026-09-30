import { auth } from '@clerk/nextjs/server'
import { redirect, notFound } from 'next/navigation'
import DashboardCategoriesIdClient from './page-client'
import { categoryService } from '@/lib/services/category.service'

export const dynamic = 'force-dynamic'

export default async function DashboardCategoriesIdPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const item = await categoryService.getByIdWithRelations(userId, id)
  if (!item) notFound()
  return <DashboardCategoriesIdClient item={item} />
}
