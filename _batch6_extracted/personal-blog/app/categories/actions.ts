// AUTO-GÉNÉRÉ PAR dev_actions_generator.py — NE PAS MODIFIER
'use server'

import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import { revalidatePath } from 'next/cache'
import { categoryService } from '@/lib/services/category.service'
import { CreateCategorySchema, UpdateCategorySchema } from '@/lib/schemas'

export async function createCategory(formData: FormData) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const validated = CreateCategorySchema.parse(Object.fromEntries(formData) as Record<string, unknown>)
  await categoryService.create(userId, validated)
  revalidatePath('/categories')
  redirect('/categories')
}

export async function updateCategory(id: string, formData: FormData) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const validated = UpdateCategorySchema.parse(Object.fromEntries(formData) as Record<string, unknown>)
  await categoryService.update(userId, id, validated)
  revalidatePath('/categories')
  redirect('/categories')
}

export async function deleteCategory(id: string) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  await categoryService.delete(userId, id)
  revalidatePath('/categories')
  redirect('/categories')
}
