import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import CategoriesClient from './page-client'
import { categoryService } from '@/lib/services/category.service'

export const dynamic = 'force-dynamic'

export default async function CategoriesPage() {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const items = await categoryService.getAll(userId)
  return <CategoriesClient items={items} />
}
