// AUTO-GÉNÉRÉ PAR dev_actions_generator.py — NE PAS MODIFIER
'use server'

import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import { revalidatePath } from 'next/cache'
import { ZodError } from 'zod'
import { categoryService } from '@/lib/services/category.service'
import { CreateCategorySchema, UpdateCategorySchema } from '@/lib/schemas'

export async function createCategory(formData: FormData) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    const validated = CreateCategorySchema.parse(Object.fromEntries(formData) as Record<string, unknown>)
    await categoryService.create(userId, validated)
  } catch (e) {
    if (e instanceof ZodError) throw new Error(e.errors.map(err => err.message).join(', '))
    throw new Error('Une erreur est survenue. Veuillez réessayer.')
  }
  revalidatePath('/dashboard/categories')
  redirect('/dashboard/categories')
}

export async function updateCategory(id: string, formData: FormData) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    const validated = UpdateCategorySchema.parse(Object.fromEntries(formData) as Record<string, unknown>)
    await categoryService.update(userId, id, validated)
  } catch (e) {
    if (e instanceof ZodError) throw new Error(e.errors.map(err => err.message).join(', '))
    throw new Error('Une erreur est survenue. Veuillez réessayer.')
  }
  revalidatePath('/dashboard/categories')
  redirect('/dashboard/categories')
}

export async function deleteCategory(id: string) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    await categoryService.delete(userId, id)
  } catch {
    return { error: 'Impossible de supprimer cet élément.' }
  }
  revalidatePath('/dashboard/categories')
  redirect('/dashboard/categories')
}
