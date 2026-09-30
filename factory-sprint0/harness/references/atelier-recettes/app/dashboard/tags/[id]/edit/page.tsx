import { auth } from '@clerk/nextjs/server'
import { redirect, notFound } from 'next/navigation'
import { tagService } from '@/lib/services/tag.service'
import { recipeService } from '@/lib/services/recipe.service'
import TagEditClient from './page-client'

export const dynamic = 'force-dynamic'

export default async function TagEditPage({ params }: { params: Promise<{ id: string }> }) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const { id } = await params
  const item = await tagService.getByIdWithRelations(userId, id)
  if (!item) notFound()
  const recipeOptions = await recipeService.getAll(userId)
  return <TagEditClient item={item} recipeOptions={recipeOptions} />
}
