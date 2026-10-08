// AUTO-GÉNÉRÉ PAR dev_actions_generator.py — NE PAS MODIFIER
'use server'

import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import { revalidatePath } from 'next/cache'
import { ZodError } from 'zod'
import { roomReservationService } from '@/lib/services/room-reservation.service'
import { CreateRoomReservationSchema, UpdateRoomReservationSchema } from '@/lib/schemas'

export async function createRoomReservation(formData: FormData) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    const validated = CreateRoomReservationSchema.parse(Object.fromEntries(formData) as Record<string, unknown>)
    await roomReservationService.create(userId, validated)
  } catch (e) {
    if (e instanceof ZodError) throw new Error(e.errors.map(err => err.message).join(', '))
    throw new Error('Une erreur est survenue. Veuillez réessayer.')
  }
  revalidatePath('/room-reservations')
  redirect('/room-reservations')
}

export async function updateRoomReservation(id: string, formData: FormData) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    const validated = UpdateRoomReservationSchema.parse(Object.fromEntries(formData) as Record<string, unknown>)
    await roomReservationService.update(userId, id, validated)
  } catch (e) {
    if (e instanceof ZodError) throw new Error(e.errors.map(err => err.message).join(', '))
    throw new Error('Une erreur est survenue. Veuillez réessayer.')
  }
  revalidatePath('/room-reservations')
  redirect('/room-reservations')
}

export async function deleteRoomReservation(id: string) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    await roomReservationService.delete(userId, id)
  } catch {
    return { error: 'Impossible de supprimer cet élément.' }
  }
  revalidatePath('/room-reservations')
  redirect('/room-reservations')
}
