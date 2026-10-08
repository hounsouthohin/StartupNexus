// AUTO-GÉNÉRÉ PAR dev_actions_generator.py — NE PAS MODIFIER
'use server'

import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import { revalidatePath } from 'next/cache'
import { ZodError } from 'zod'
import { examService } from '@/lib/services/exam.service'
import { CreateExamSchema, UpdateExamSchema } from '@/lib/schemas'

export async function createExam(formData: FormData) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    const validated = CreateExamSchema.parse(Object.fromEntries(formData) as Record<string, unknown>)
    await examService.create(userId, validated)
  } catch (e) {
    if (e instanceof ZodError) throw new Error(e.errors.map(err => err.message).join(', '))
    throw new Error('Une erreur est survenue. Veuillez réessayer.')
  }
  revalidatePath('/exams')
  redirect('/exams')
}

export async function updateExam(id: string, formData: FormData) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    const validated = UpdateExamSchema.parse(Object.fromEntries(formData) as Record<string, unknown>)
    await examService.update(userId, id, validated)
  } catch (e) {
    if (e instanceof ZodError) throw new Error(e.errors.map(err => err.message).join(', '))
    throw new Error('Une erreur est survenue. Veuillez réessayer.')
  }
  revalidatePath('/exams')
  redirect('/exams')
}

export async function deleteExam(id: string) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    await examService.delete(userId, id)
  } catch {
    return { error: 'Impossible de supprimer cet élément.' }
  }
  revalidatePath('/exams')
  redirect('/exams')
}
