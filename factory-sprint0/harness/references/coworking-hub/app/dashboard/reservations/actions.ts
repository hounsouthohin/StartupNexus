// AUTO-GÉNÉRÉ PAR dev_actions_generator.py — NE PAS MODIFIER
'use server'

import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import { revalidatePath } from 'next/cache'
import { ZodError } from 'zod'
import { reservationService } from '@/lib/services/reservation.service'
import { CreateReservationSchema, UpdateReservationSchema } from '@/lib/schemas'
import { requireRole, hasRole } from '@/lib/auth-role'

export async function createReservation(formData: FormData) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  if (await hasRole('admin')) throw new Error('Création réservée aux members — le rôle admin ne crée pas cette entité.')
  try {
    const validated = CreateReservationSchema.parse(Object.fromEntries(formData) as Record<string, unknown>)
    await reservationService.create(userId, validated)
  } catch (e) {
    if (e instanceof ZodError) throw new Error(e.errors.map(err => err.message).join(', '))
    throw new Error('Une erreur est survenue. Veuillez réessayer.')
  }
  revalidatePath('/dashboard/reservations')
  redirect('/dashboard/reservations')
}

export async function updateReservation(id: string, formData: FormData) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    const validated = UpdateReservationSchema.parse(Object.fromEntries(formData) as Record<string, unknown>)
    await reservationService.update(userId, id, validated)
  } catch (e) {
    if (e instanceof ZodError) throw new Error(e.errors.map(err => err.message).join(', '))
    throw new Error('Une erreur est survenue. Veuillez réessayer.')
  }
  revalidatePath('/dashboard/reservations')
  redirect('/dashboard/reservations')
}

export async function transitionReservation(id: string, newStatus: string, formData: FormData) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  await requireRole('admin')
  try {
    const data = UpdateReservationSchema.parse(Object.fromEntries(formData) as Record<string, unknown>)
    await reservationService.transitionTo(userId, id, newStatus, data)
  } catch (e) {
    if (e instanceof ZodError) throw new Error(e.errors.map(err => err.message).join(', '))
    throw new Error('Une erreur est survenue. Veuillez réessayer.')
  }
  revalidatePath('/dashboard/reservations')
  redirect('/dashboard/reservations')
}

export async function deleteReservation(id: string) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    await reservationService.delete(userId, id)
  } catch {
    return { error: 'Impossible de supprimer cet élément.' }
  }
  revalidatePath('/dashboard/reservations')
  redirect('/dashboard/reservations')
}
