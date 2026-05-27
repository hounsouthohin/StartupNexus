import { auth } from '@clerk/nextjs/server'
import { redirect, notFound } from 'next/navigation'
import CategoriesIdClient from './page-client'
import { categoryService } from '@/lib/services/category.service'

export const dynamic = 'force-dynamic'

export default async function CategoriesIdPage({ params }: { params: { id: string } }) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const item = await categoryService.getById(userId, params.id)
  if (!item) notFound()
  return <CategoriesIdClient item={item} />
}
