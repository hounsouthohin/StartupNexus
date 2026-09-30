import { auth } from '@clerk/nextjs/server'
import { redirect, notFound } from 'next/navigation'
import { recipeService } from '@/lib/services/recipe.service'
import { tagService } from '@/lib/services/tag.service'
import RecipeEditClient from './page-client'

export const dynamic = 'force-dynamic'

export default async function RecipeEditPage({ params }: { params: Promise<{ slug: string }> }) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const { slug } = await params
  const item = await recipeService.getBySlugOwned(userId, slug)
  if (!item) notFound()
  const tagOptions = await tagService.getAll(userId)
  return <RecipeEditClient item={item} tagOptions={tagOptions} />
}
