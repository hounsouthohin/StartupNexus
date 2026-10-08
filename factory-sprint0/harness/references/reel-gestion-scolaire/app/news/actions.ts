// AUTO-GÉNÉRÉ PAR dev_actions_generator.py — NE PAS MODIFIER
'use server'

import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import { revalidatePath } from 'next/cache'
import { ZodError } from 'zod'
import { newsService } from '@/lib/services/news.service'
import { CreateNewsSchema, UpdateNewsSchema } from '@/lib/schemas'

export async function createNews(formData: FormData) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    const validated = CreateNewsSchema.parse(Object.fromEntries(formData) as Record<string, unknown>)
    await newsService.create(userId, validated)
  } catch (e) {
    if (e instanceof ZodError) throw new Error(e.errors.map(err => err.message).join(', '))
    throw new Error('Une erreur est survenue. Veuillez réessayer.')
  }
  revalidatePath('/news')
  redirect('/news')
}

export async function updateNews(id: string, formData: FormData) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    const validated = UpdateNewsSchema.parse(Object.fromEntries(formData) as Record<string, unknown>)
    await newsService.update(userId, id, validated)
  } catch (e) {
    if (e instanceof ZodError) throw new Error(e.errors.map(err => err.message).join(', '))
    throw new Error('Une erreur est survenue. Veuillez réessayer.')
  }
  revalidatePath('/news')
  redirect('/news')
}

export async function deleteNews(id: string) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    await newsService.delete(userId, id)
  } catch {
    return { error: 'Impossible de supprimer cet élément.' }
  }
  revalidatePath('/news')
  redirect('/news')
}
