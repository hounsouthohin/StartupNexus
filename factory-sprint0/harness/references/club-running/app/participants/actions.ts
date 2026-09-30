// AUTO-GÉNÉRÉ PAR dev_actions_generator.py — NE PAS MODIFIER
'use server'

import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import { revalidatePath } from 'next/cache'
import { ZodError } from 'zod'
import { participantService } from '@/lib/services/participant.service'
import { CreateParticipantSchema, UpdateParticipantSchema } from '@/lib/schemas'

export async function createParticipant(formData: FormData) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    const validated = CreateParticipantSchema.parse(Object.fromEntries(formData) as Record<string, unknown>)
    await participantService.create(userId, validated)
    revalidatePath(`/dashboard/run-events/${validated.runEventId}`)
    redirect(`/dashboard/run-events/${validated.runEventId}`)
  } catch (e) {
    if (e instanceof ZodError) throw new Error(e.errors.map(err => err.message).join(', '))
    throw new Error('Une erreur est survenue. Veuillez réessayer.')
  }
}

export async function updateParticipant(id: string, formData: FormData) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    const validated = UpdateParticipantSchema.parse(Object.fromEntries(formData) as Record<string, unknown>)
    await participantService.update(userId, id, validated)
  } catch (e) {
    if (e instanceof ZodError) throw new Error(e.errors.map(err => err.message).join(', '))
    throw new Error('Une erreur est survenue. Veuillez réessayer.')
  }
  const redirectTo = (formData.get('_redirectTo') as string) || '/dashboard/run-events'
  revalidatePath(redirectTo)
  redirect(redirectTo)
}

export async function deleteParticipant(id: string, redirectTo: string = '/dashboard/run-events') {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    await participantService.delete(userId, id)
  } catch {
    return { error: 'Impossible de supprimer cet élément.' }
  }
  revalidatePath(redirectTo)
  redirect(redirectTo)
}
