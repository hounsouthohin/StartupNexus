// AUTO-GÉNÉRÉ PAR dev_actions_generator.py — NE PAS MODIFIER
'use server'

import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import { revalidatePath } from 'next/cache'
import { recipeService } from '@/lib/services/recipe.service'
import { CreateRecipeSchema, UpdateRecipeSchema } from '@/lib/schemas'

export async function createRecipe(formData: FormData) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const validated = CreateRecipeSchema.parse(Object.fromEntries(formData) as Record<string, unknown>)
  await recipeService.create(userId, validated)
  revalidatePath('/dashboard/recipes')
  redirect('/dashboard/recipes')
}

export async function updateRecipe(id: string, formData: FormData) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const validated = UpdateRecipeSchema.parse(Object.fromEntries(formData) as Record<string, unknown>)
  await recipeService.update(userId, id, validated)
  revalidatePath('/dashboard/recipes')
  redirect('/dashboard/recipes')
}

export async function deleteRecipe(id: string) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  await recipeService.delete(userId, id)
  revalidatePath('/dashboard/recipes')
  redirect('/dashboard/recipes')
}
