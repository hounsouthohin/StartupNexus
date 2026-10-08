// AUTO-GÉNÉRÉ PAR dev_actions_generator.py — NE PAS MODIFIER
'use server'

import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import { revalidatePath } from 'next/cache'
import { ZodError } from 'zod'
import { timetableService } from '@/lib/services/timetable.service'
import { CreateTimetableSchema, UpdateTimetableSchema } from '@/lib/schemas'

export async function createTimetable(formData: FormData) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    const validated = CreateTimetableSchema.parse(Object.fromEntries(formData) as Record<string, unknown>)
    await timetableService.create(userId, validated)
  } catch (e) {
    if (e instanceof ZodError) throw new Error(e.errors.map(err => err.message).join(', '))
    throw new Error('Une erreur est survenue. Veuillez réessayer.')
  }
  revalidatePath('/timetables')
  redirect('/timetables')
}

export async function updateTimetable(id: string, formData: FormData) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    const validated = UpdateTimetableSchema.parse(Object.fromEntries(formData) as Record<string, unknown>)
    await timetableService.update(userId, id, validated)
  } catch (e) {
    if (e instanceof ZodError) throw new Error(e.errors.map(err => err.message).join(', '))
    throw new Error('Une erreur est survenue. Veuillez réessayer.')
  }
  revalidatePath('/timetables')
  redirect('/timetables')
}

export async function deleteTimetable(id: string) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    await timetableService.delete(userId, id)
  } catch {
    return { error: 'Impossible de supprimer cet élément.' }
  }
  revalidatePath('/timetables')
  redirect('/timetables')
}
