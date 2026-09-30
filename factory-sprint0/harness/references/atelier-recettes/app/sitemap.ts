// AUTO-GÉNÉRÉ PAR dev_seo_generator.py — NE PAS MODIFIER
import type { MetadataRoute } from 'next'
import { recipeService } from '@/lib/services/recipe.service'

const BASE = process.env.NEXT_PUBLIC_APP_URL ?? 'http://localhost:3000'

export const dynamic = 'force-dynamic'

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const entries: MetadataRoute.Sitemap = [
    { url: BASE, lastModified: new Date() },
    { url: `${BASE}/recipes`, lastModified: new Date() },
  ]
  const recipes = await recipeService.getPublicAll()
  entries.push(...recipes.map(item => ({
    url: `${BASE}/recipes/${item.slug}`,
    lastModified: item.updatedAt ? new Date(item.updatedAt) : new Date(),
  })))
  return entries
}
