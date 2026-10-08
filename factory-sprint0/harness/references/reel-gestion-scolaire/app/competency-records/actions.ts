// AUTO-GÉNÉRÉ PAR dev_actions_generator.py — NE PAS MODIFIER
'use server'

import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import { revalidatePath } from 'next/cache'
import { ZodError } from 'zod'
import { competencyRecordService } from '@/lib/services/competency-record.service'
import { CreateCompetencyRecordSchema, UpdateCompetencyRecordSchema } from '@/lib/schemas'

export async function createCompetencyRecord(formData: FormData) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    const validated = CreateCompetencyRecordSchema.parse(Object.fromEntries(formData) as Record<string, unknown>)
    await competencyRecordService.create(userId, validated)
  } catch (e) {
    if (e instanceof ZodError) throw new Error(e.errors.map(err => err.message).join(', '))
    throw new Error('Une erreur est survenue. Veuillez réessayer.')
  }
  revalidatePath('/competency-records')
  redirect('/competency-records')
}

export async function updateCompetencyRecord(id: string, formData: FormData) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    const validated = UpdateCompetencyRecordSchema.parse(Object.fromEntries(formData) as Record<string, unknown>)
    await competencyRecordService.update(userId, id, validated)
  } catch (e) {
    if (e instanceof ZodError) throw new Error(e.errors.map(err => err.message).join(', '))
    throw new Error('Une erreur est survenue. Veuillez réessayer.')
  }
  revalidatePath('/competency-records')
  redirect('/competency-records')
}

export async function deleteCompetencyRecord(id: string) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    await competencyRecordService.delete(userId, id)
  } catch {
    return { error: 'Impossible de supprimer cet élément.' }
  }
  revalidatePath('/competency-records')
  redirect('/competency-records')
}
