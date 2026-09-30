import type { Metadata } from 'next'
import { notFound } from 'next/navigation'
import RecipesSlugClient from './page-client'
import { recipeService } from '@/lib/services/recipe.service'

export const dynamic = 'force-dynamic'

export async function generateMetadata({ params }: { params: Promise<{ slug: string }> }): Promise<Metadata> {
  const { slug } = await params
  const item = await recipeService.getBySlug(slug)
  const title = String(item.title ?? 'Recipe')
  const description = String(item.instructions ?? '').slice(0, 160)
  return {
    title,
    description,
    openGraph: { title, description, type: 'article' },
  }
}

export default async function RecipesSlugPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params
  const item = await recipeService.getBySlugWithRelations(slug)
  if (!item) notFound()
  return <RecipesSlugClient item={item} />
}
