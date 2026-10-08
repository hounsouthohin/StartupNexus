// AUTO-GÉNÉRÉ PAR dev_actions_generator.py — NE PAS MODIFIER
'use server'

import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import { revalidatePath } from 'next/cache'
import { ZodError } from 'zod'
import { absenceService } from '@/lib/services/absence.service'
import { CreateAbsenceSchema, UpdateAbsenceSchema } from '@/lib/schemas'

export async function createAbsence(formData: FormData) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    const validated = CreateAbsenceSchema.parse(Object.fromEntries(formData) as Record<string, unknown>)
    await absenceService.create(userId, validated)
  } catch (e) {
    if (e instanceof ZodError) throw new Error(e.errors.map(err => err.message).join(', '))
    throw new Error('Une erreur est survenue. Veuillez réessayer.')
  }
  revalidatePath('/absences')
  redirect('/absences')
}

export async function updateAbsence(id: string, formData: FormData) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    const validated = UpdateAbsenceSchema.parse(Object.fromEntries(formData) as Record<string, unknown>)
    await absenceService.update(userId, id, validated)
  } catch (e) {
    if (e instanceof ZodError) throw new Error(e.errors.map(err => err.message).join(', '))
    throw new Error('Une erreur est survenue. Veuillez réessayer.')
  }
  revalidatePath('/absences')
  redirect('/absences')
}

export async function deleteAbsence(id: string) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    await absenceService.delete(userId, id)
  } catch {
    return { error: 'Impossible de supprimer cet élément.' }
  }
  revalidatePath('/absences')
  redirect('/absences')
}
