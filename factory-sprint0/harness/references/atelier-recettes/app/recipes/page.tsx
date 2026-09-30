import RecipesClient from './page-client'
import { recipeService } from '@/lib/services/recipe.service'

export const dynamic = 'force-dynamic'

export default async function RecipesPage() {
  const items = await recipeService.getPublicAll()
  return <RecipesClient items={items} />
}
