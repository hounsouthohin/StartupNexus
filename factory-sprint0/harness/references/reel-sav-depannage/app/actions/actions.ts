// AUTO-GÉNÉRÉ PAR dev_actions_generator.py — NE PAS MODIFIER
'use server'

import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import { revalidatePath } from 'next/cache'
import { ZodError } from 'zod'
import { actionService } from '@/lib/services/action.service'
import { CreateActionSchema, UpdateActionSchema } from '@/lib/schemas'

export async function createAction(formData: FormData) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    const validated = CreateActionSchema.parse(Object.fromEntries(formData) as Record<string, unknown>)
    await actionService.create(userId, validated)
  } catch (e) {
    if (e instanceof ZodError) throw new Error(e.errors.map(err => err.message).join(', '))
    throw new Error('Une erreur est survenue. Veuillez réessayer.')
  }
  revalidatePath('/actions')
  redirect('/actions')
}

export async function updateAction(id: string, formData: FormData) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    const validated = UpdateActionSchema.parse(Object.fromEntries(formData) as Record<string, unknown>)
    await actionService.update(userId, id, validated)
  } catch (e) {
    if (e instanceof ZodError) throw new Error(e.errors.map(err => err.message).join(', '))
    throw new Error('Une erreur est survenue. Veuillez réessayer.')
  }
  revalidatePath('/actions')
  redirect('/actions')
}

export async function transitionAction(id: string, newStatus: string, formData: FormData) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    const data = UpdateActionSchema.parse(Object.fromEntries(formData) as Record<string, unknown>)
    await actionService.transitionTo(userId, id, newStatus, data)
  } catch (e) {
    if (e instanceof ZodError) throw new Error(e.errors.map(err => err.message).join(', '))
    throw new Error('Une erreur est survenue. Veuillez réessayer.')
  }
  revalidatePath('/actions')
  redirect('/actions')
}

export async function deleteAction(id: string) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    await actionService.delete(userId, id)
  } catch {
    return { error: 'Impossible de supprimer cet élément.' }
  }
  revalidatePath('/actions')
  redirect('/actions')
}
