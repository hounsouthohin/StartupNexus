// AUTO-GÉNÉRÉ PAR dev_actions_generator.py — NE PAS MODIFIER
'use server'

import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import { revalidatePath } from 'next/cache'
import { ZodError } from 'zod'
import { spaceService } from '@/lib/services/space.service'
import { CreateSpaceSchema, UpdateSpaceSchema } from '@/lib/schemas'

export async function createSpace(formData: FormData) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    const validated = CreateSpaceSchema.parse(Object.fromEntries(formData) as Record<string, unknown>)
    await spaceService.create(userId, validated)
  } catch (e) {
    if (e instanceof ZodError) throw new Error(e.errors.map(err => err.message).join(', '))
    throw new Error('Une erreur est survenue. Veuillez réessayer.')
  }
  revalidatePath('/spaces')
  redirect('/spaces')
}

export async function updateSpace(id: string, formData: FormData) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    const validated = UpdateSpaceSchema.parse(Object.fromEntries(formData) as Record<string, unknown>)
    await spaceService.update(userId, id, validated)
  } catch (e) {
    if (e instanceof ZodError) throw new Error(e.errors.map(err => err.message).join(', '))
    throw new Error('Une erreur est survenue. Veuillez réessayer.')
  }
  revalidatePath('/spaces')
  redirect('/spaces')
}

export async function deleteSpace(id: string) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    await spaceService.delete(userId, id)
  } catch {
    return { error: 'Impossible de supprimer cet élément.' }
  }
  revalidatePath('/spaces')
  redirect('/spaces')
}
