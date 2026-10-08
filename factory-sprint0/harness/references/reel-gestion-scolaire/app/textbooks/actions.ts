// AUTO-GÉNÉRÉ PAR dev_actions_generator.py — NE PAS MODIFIER
'use server'

import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import { revalidatePath } from 'next/cache'
import { ZodError } from 'zod'
import { textbookService } from '@/lib/services/textbook.service'
import { CreateTextbookSchema, UpdateTextbookSchema } from '@/lib/schemas'

export async function createTextbook(formData: FormData) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    const validated = CreateTextbookSchema.parse(Object.fromEntries(formData) as Record<string, unknown>)
    await textbookService.create(userId, validated)
  } catch (e) {
    if (e instanceof ZodError) throw new Error(e.errors.map(err => err.message).join(', '))
    throw new Error('Une erreur est survenue. Veuillez réessayer.')
  }
  revalidatePath('/textbooks')
  redirect('/textbooks')
}

export async function updateTextbook(id: string, formData: FormData) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    const validated = UpdateTextbookSchema.parse(Object.fromEntries(formData) as Record<string, unknown>)
    await textbookService.update(userId, id, validated)
  } catch (e) {
    if (e instanceof ZodError) throw new Error(e.errors.map(err => err.message).join(', '))
    throw new Error('Une erreur est survenue. Veuillez réessayer.')
  }
  revalidatePath('/textbooks')
  redirect('/textbooks')
}

export async function deleteTextbook(id: string) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    await textbookService.delete(userId, id)
  } catch {
    return { error: 'Impossible de supprimer cet élément.' }
  }
  revalidatePath('/textbooks')
  redirect('/textbooks')
}
