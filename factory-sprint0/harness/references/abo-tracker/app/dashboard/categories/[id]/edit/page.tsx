import { auth } from '@clerk/nextjs/server'
import { redirect, notFound } from 'next/navigation'
import { categoryService } from '@/lib/services/category.service'
import CategoryEditClient from './page-client'

export const dynamic = 'force-dynamic'

export default async function CategoryEditPage({ params }: { params: Promise<{ id: string }> }) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const { id } = await params
  const item = await categoryService.getById(userId, id)
  if (!item) notFound()
  return <CategoryEditClient item={item} />
}
