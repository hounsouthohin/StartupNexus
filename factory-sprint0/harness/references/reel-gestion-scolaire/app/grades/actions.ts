// AUTO-GÉNÉRÉ PAR dev_actions_generator.py — NE PAS MODIFIER
'use server'

import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import { revalidatePath } from 'next/cache'
import { ZodError } from 'zod'
import { gradeService } from '@/lib/services/grade.service'
import { CreateGradeSchema, UpdateGradeSchema } from '@/lib/schemas'

export async function createGrade(formData: FormData) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    const validated = CreateGradeSchema.parse(Object.fromEntries(formData) as Record<string, unknown>)
    await gradeService.create(userId, validated)
  } catch (e) {
    if (e instanceof ZodError) throw new Error(e.errors.map(err => err.message).join(', '))
    throw new Error('Une erreur est survenue. Veuillez réessayer.')
  }
  revalidatePath('/grades')
  redirect('/grades')
}

export async function updateGrade(id: string, formData: FormData) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    const validated = UpdateGradeSchema.parse(Object.fromEntries(formData) as Record<string, unknown>)
    await gradeService.update(userId, id, validated)
  } catch (e) {
    if (e instanceof ZodError) throw new Error(e.errors.map(err => err.message).join(', '))
    throw new Error('Une erreur est survenue. Veuillez réessayer.')
  }
  revalidatePath('/grades')
  redirect('/grades')
}

export async function deleteGrade(id: string) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    await gradeService.delete(userId, id)
  } catch {
    return { error: 'Impossible de supprimer cet élément.' }
  }
  revalidatePath('/grades')
  redirect('/grades')
}
