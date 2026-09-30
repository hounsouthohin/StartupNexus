import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import DashboardRecipesClient from './page-client'
import { recipeService } from '@/lib/services/recipe.service'

export const dynamic = 'force-dynamic'

export default async function DashboardRecipesPage() {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const items = await recipeService.getAllWithRelations(userId)
  return <DashboardRecipesClient items={items} />
}
