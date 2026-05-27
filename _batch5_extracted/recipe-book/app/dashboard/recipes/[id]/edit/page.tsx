import { auth } from '@clerk/nextjs/server'
import { redirect, notFound } from 'next/navigation'
import { recipeService } from '@/lib/services/recipe.service'
import { categoryService } from '@/lib/services/category.service'
import RecipeEditClient from './page-client'

export const dynamic = 'force-dynamic'

export default async function RecipeEditPage({ params }: { params: { id: string } }) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const item = await recipeService.getById(userId, params.id)
  if (!item) notFound()
  const categoryOptions = await categoryService.getAll(userId)
  return <RecipeEditClient item={item} categoryOptions={categoryOptions} />
}
