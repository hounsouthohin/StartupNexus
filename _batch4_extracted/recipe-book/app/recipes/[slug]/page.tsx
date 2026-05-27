import { notFound } from 'next/navigation'
import RecipesSlugClient from './page-client'
import { recipeService } from '@/lib/services/recipe.service'

export const dynamic = 'force-dynamic'

export default async function RecipesSlugPage({ params }: { params: { slug: string } }) {
  const item = await recipeService.getBySlugWithRelations(params.slug)
  if (!item) notFound()
  return <RecipesSlugClient item={item} />
}
