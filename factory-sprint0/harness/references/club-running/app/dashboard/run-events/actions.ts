// AUTO-GÉNÉRÉ PAR dev_actions_generator.py — NE PAS MODIFIER
'use server'

import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import { revalidatePath } from 'next/cache'
import { ZodError } from 'zod'
import { runEventService } from '@/lib/services/run-event.service'
import { CreateRunEventSchema, UpdateRunEventSchema } from '@/lib/schemas'

export async function createRunEvent(formData: FormData) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    const validated = CreateRunEventSchema.parse(Object.fromEntries(formData) as Record<string, unknown>)
    await runEventService.create(userId, validated)
  } catch (e) {
    if (e instanceof ZodError) throw new Error(e.errors.map(err => err.message).join(', '))
    throw new Error('Une erreur est survenue. Veuillez réessayer.')
  }
  revalidatePath('/dashboard/run-events')
  redirect('/dashboard/run-events')
}

export async function updateRunEvent(id: string, formData: FormData) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    const validated = UpdateRunEventSchema.parse(Object.fromEntries(formData) as Record<string, unknown>)
    await runEventService.update(userId, id, validated)
  } catch (e) {
    if (e instanceof ZodError) throw new Error(e.errors.map(err => err.message).join(', '))
    throw new Error('Une erreur est survenue. Veuillez réessayer.')
  }
  revalidatePath('/dashboard/run-events')
  redirect('/dashboard/run-events')
}

export async function transitionRunEvent(id: string, newStatus: string, formData: FormData) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    const data = UpdateRunEventSchema.parse(Object.fromEntries(formData) as Record<string, unknown>)
    await runEventService.transitionTo(userId, id, newStatus, data)
  } catch (e) {
    if (e instanceof ZodError) throw new Error(e.errors.map(err => err.message).join(', '))
    throw new Error('Une erreur est survenue. Veuillez réessayer.')
  }
  revalidatePath('/dashboard/run-events')
  redirect('/dashboard/run-events')
}

export async function deleteRunEvent(id: string) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    await runEventService.delete(userId, id)
  } catch {
    return { error: 'Impossible de supprimer cet élément.' }
  }
  revalidatePath('/dashboard/run-events')
  redirect('/dashboard/run-events')
}
