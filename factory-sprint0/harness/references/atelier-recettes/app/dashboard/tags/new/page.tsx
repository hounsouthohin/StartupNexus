import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import DashboardTagsNewClient from './page-client'
import { recipeService } from '@/lib/services/recipe.service'

export const dynamic = 'force-dynamic'

export default async function DashboardTagsNewPage() {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const recipeOptions = await recipeService.getAll(userId)
  return <DashboardTagsNewClient recipeOptions={recipeOptions} />
}
