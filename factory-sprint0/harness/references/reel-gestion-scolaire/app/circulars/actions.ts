// AUTO-GÉNÉRÉ PAR dev_actions_generator.py — NE PAS MODIFIER
'use server'

import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import { revalidatePath } from 'next/cache'
import { ZodError } from 'zod'
import { circularService } from '@/lib/services/circular.service'
import { CreateCircularSchema, UpdateCircularSchema } from '@/lib/schemas'

export async function createCircular(formData: FormData) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    const validated = CreateCircularSchema.parse(Object.fromEntries(formData) as Record<string, unknown>)
    await circularService.create(userId, validated)
  } catch (e) {
    if (e instanceof ZodError) throw new Error(e.errors.map(err => err.message).join(', '))
    throw new Error('Une erreur est survenue. Veuillez réessayer.')
  }
  revalidatePath('/circulars')
  redirect('/circulars')
}

export async function updateCircular(id: string, formData: FormData) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    const validated = UpdateCircularSchema.parse(Object.fromEntries(formData) as Record<string, unknown>)
    await circularService.update(userId, id, validated)
  } catch (e) {
    if (e instanceof ZodError) throw new Error(e.errors.map(err => err.message).join(', '))
    throw new Error('Une erreur est survenue. Veuillez réessayer.')
  }
  revalidatePath('/circulars')
  redirect('/circulars')
}

export async function deleteCircular(id: string) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    await circularService.delete(userId, id)
  } catch {
    return { error: 'Impossible de supprimer cet élément.' }
  }
  revalidatePath('/circulars')
  redirect('/circulars')
}
