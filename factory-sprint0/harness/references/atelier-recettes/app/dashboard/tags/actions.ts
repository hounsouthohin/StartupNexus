// AUTO-GÉNÉRÉ PAR dev_actions_generator.py — NE PAS MODIFIER
'use server'

import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import { revalidatePath } from 'next/cache'
import { ZodError } from 'zod'
import { tagService } from '@/lib/services/tag.service'
import { CreateTagSchema, UpdateTagSchema } from '@/lib/schemas'

export async function createTag(formData: FormData) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    const _raw = Object.fromEntries(formData) as Record<string, unknown>
    _raw.recipeIds = formData.getAll('recipeIds').map(String).filter(v => v.length > 0)
    const validated = CreateTagSchema.parse(_raw)
    await tagService.create(userId, validated)
  } catch (e) {
    if (e instanceof ZodError) throw new Error(e.errors.map(err => err.message).join(', '))
    throw new Error('Une erreur est survenue. Veuillez réessayer.')
  }
  revalidatePath('/dashboard/tags')
  redirect('/dashboard/tags')
}

export async function updateTag(id: string, formData: FormData) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    const _raw = Object.fromEntries(formData) as Record<string, unknown>
    _raw.recipeIds = formData.getAll('recipeIds').map(String).filter(v => v.length > 0)
    const validated = UpdateTagSchema.parse(_raw)
    await tagService.update(userId, id, validated)
  } catch (e) {
    if (e instanceof ZodError) throw new Error(e.errors.map(err => err.message).join(', '))
    throw new Error('Une erreur est survenue. Veuillez réessayer.')
  }
  revalidatePath('/dashboard/tags')
  redirect('/dashboard/tags')
}

export async function deleteTag(id: string) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    await tagService.delete(userId, id)
  } catch {
    return { error: 'Impossible de supprimer cet élément.' }
  }
  revalidatePath('/dashboard/tags')
  redirect('/dashboard/tags')
}
