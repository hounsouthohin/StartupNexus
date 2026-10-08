// AUTO-GÉNÉRÉ PAR dev_actions_generator.py — NE PAS MODIFIER
'use server'

import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import { revalidatePath } from 'next/cache'
import { ZodError } from 'zod'
import { delayService } from '@/lib/services/delay.service'
import { CreateDelaySchema, UpdateDelaySchema } from '@/lib/schemas'

export async function createDelay(formData: FormData) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    const validated = CreateDelaySchema.parse(Object.fromEntries(formData) as Record<string, unknown>)
    await delayService.create(userId, validated)
  } catch (e) {
    if (e instanceof ZodError) throw new Error(e.errors.map(err => err.message).join(', '))
    throw new Error('Une erreur est survenue. Veuillez réessayer.')
  }
  revalidatePath('/delays')
  redirect('/delays')
}

export async function updateDelay(id: string, formData: FormData) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    const validated = UpdateDelaySchema.parse(Object.fromEntries(formData) as Record<string, unknown>)
    await delayService.update(userId, id, validated)
  } catch (e) {
    if (e instanceof ZodError) throw new Error(e.errors.map(err => err.message).join(', '))
    throw new Error('Une erreur est survenue. Veuillez réessayer.')
  }
  revalidatePath('/delays')
  redirect('/delays')
}

export async function deleteDelay(id: string) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    await delayService.delete(userId, id)
  } catch {
    return { error: 'Impossible de supprimer cet élément.' }
  }
  revalidatePath('/delays')
  redirect('/delays')
}
