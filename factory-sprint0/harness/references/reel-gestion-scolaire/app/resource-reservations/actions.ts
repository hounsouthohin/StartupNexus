// AUTO-GÉNÉRÉ PAR dev_actions_generator.py — NE PAS MODIFIER
'use server'

import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import { revalidatePath } from 'next/cache'
import { ZodError } from 'zod'
import { resourceReservationService } from '@/lib/services/resource-reservation.service'
import { CreateResourceReservationSchema, UpdateResourceReservationSchema } from '@/lib/schemas'

export async function createResourceReservation(formData: FormData) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    const validated = CreateResourceReservationSchema.parse(Object.fromEntries(formData) as Record<string, unknown>)
    await resourceReservationService.create(userId, validated)
  } catch (e) {
    if (e instanceof ZodError) throw new Error(e.errors.map(err => err.message).join(', '))
    throw new Error('Une erreur est survenue. Veuillez réessayer.')
  }
  revalidatePath('/resource-reservations')
  redirect('/resource-reservations')
}

export async function updateResourceReservation(id: string, formData: FormData) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    const validated = UpdateResourceReservationSchema.parse(Object.fromEntries(formData) as Record<string, unknown>)
    await resourceReservationService.update(userId, id, validated)
  } catch (e) {
    if (e instanceof ZodError) throw new Error(e.errors.map(err => err.message).join(', '))
    throw new Error('Une erreur est survenue. Veuillez réessayer.')
  }
  revalidatePath('/resource-reservations')
  redirect('/resource-reservations')
}

export async function deleteResourceReservation(id: string) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    await resourceReservationService.delete(userId, id)
  } catch {
    return { error: 'Impossible de supprimer cet élément.' }
  }
  revalidatePath('/resource-reservations')
  redirect('/resource-reservations')
}
