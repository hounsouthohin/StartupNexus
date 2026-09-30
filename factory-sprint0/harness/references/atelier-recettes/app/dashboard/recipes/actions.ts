// AUTO-GÉNÉRÉ PAR dev_actions_generator.py — NE PAS MODIFIER
'use server'

import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import { revalidatePath } from 'next/cache'
import { ZodError } from 'zod'
import { recipeService } from '@/lib/services/recipe.service'
import { CreateRecipeSchema, UpdateRecipeSchema } from '@/lib/schemas'

export async function createRecipe(formData: FormData) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    const _raw = Object.fromEntries(formData) as Record<string, unknown>
    _raw.tagIds = formData.getAll('tagIds').map(String).filter(v => v.length > 0)
    const validated = CreateRecipeSchema.parse(_raw)
    await recipeService.create(userId, validated)
  } catch (e) {
    if (e instanceof ZodError) throw new Error(e.errors.map(err => err.message).join(', '))
    throw new Error('Une erreur est survenue. Veuillez réessayer.')
  }
  revalidatePath('/dashboard/recipes')
  redirect('/dashboard/recipes')
}

export async function updateRecipe(id: string, formData: FormData) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    const _raw = Object.fromEntries(formData) as Record<string, unknown>
    _raw.tagIds = formData.getAll('tagIds').map(String).filter(v => v.length > 0)
    const validated = UpdateRecipeSchema.parse(_raw)
    await recipeService.update(userId, id, validated)
  } catch (e) {
    if (e instanceof ZodError) throw new Error(e.errors.map(err => err.message).join(', '))
    throw new Error('Une erreur est survenue. Veuillez réessayer.')
  }
  revalidatePath('/dashboard/recipes')
  redirect('/dashboard/recipes')
}

export async function deleteRecipe(id: string) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    await recipeService.delete(userId, id)
  } catch {
    return { error: 'Impossible de supprimer cet élément.' }
  }
  revalidatePath('/dashboard/recipes')
  redirect('/dashboard/recipes')
}
