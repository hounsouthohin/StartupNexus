// AUTO-GÉNÉRÉ PAR dev_actions_generator.py — NE PAS MODIFIER
'use server'

import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import { revalidatePath } from 'next/cache'
import { ZodError } from 'zod'
import { continuousAssessmentService } from '@/lib/services/continuous-assessment.service'
import { CreateContinuousAssessmentSchema, UpdateContinuousAssessmentSchema } from '@/lib/schemas'

export async function createContinuousAssessment(formData: FormData) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    const validated = CreateContinuousAssessmentSchema.parse(Object.fromEntries(formData) as Record<string, unknown>)
    await continuousAssessmentService.create(userId, validated)
  } catch (e) {
    if (e instanceof ZodError) throw new Error(e.errors.map(err => err.message).join(', '))
    throw new Error('Une erreur est survenue. Veuillez réessayer.')
  }
  revalidatePath('/continuous-assessments')
  redirect('/continuous-assessments')
}

export async function updateContinuousAssessment(id: string, formData: FormData) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    const validated = UpdateContinuousAssessmentSchema.parse(Object.fromEntries(formData) as Record<string, unknown>)
    await continuousAssessmentService.update(userId, id, validated)
  } catch (e) {
    if (e instanceof ZodError) throw new Error(e.errors.map(err => err.message).join(', '))
    throw new Error('Une erreur est survenue. Veuillez réessayer.')
  }
  revalidatePath('/continuous-assessments')
  redirect('/continuous-assessments')
}

export async function deleteContinuousAssessment(id: string) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    await continuousAssessmentService.delete(userId, id)
  } catch {
    return { error: 'Impossible de supprimer cet élément.' }
  }
  revalidatePath('/continuous-assessments')
  redirect('/continuous-assessments')
}
