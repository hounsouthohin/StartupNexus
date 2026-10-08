// AUTO-GÉNÉRÉ PAR dev_actions_generator.py — NE PAS MODIFIER
'use server'

import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import { revalidatePath } from 'next/cache'
import { ZodError } from 'zod'
import { courseService } from '@/lib/services/course.service'
import { CreateCourseSchema, UpdateCourseSchema } from '@/lib/schemas'
import { requireRole, hasRole } from '@/lib/auth-role'

export async function createCourse(formData: FormData) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    const validated = CreateCourseSchema.parse(Object.fromEntries(formData) as Record<string, unknown>)
    await courseService.create(userId, validated)
  } catch (e) {
    if (e instanceof ZodError) throw new Error(e.errors.map(err => err.message).join(', '))
    throw new Error('Une erreur est survenue. Veuillez réessayer.')
  }
  revalidatePath('/courses')
  redirect('/courses')
}

export async function updateCourse(id: string, formData: FormData) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    const validated = UpdateCourseSchema.parse(Object.fromEntries(formData) as Record<string, unknown>)
    await courseService.update(userId, id, validated)
  } catch (e) {
    if (e instanceof ZodError) throw new Error(e.errors.map(err => err.message).join(', '))
    throw new Error('Une erreur est survenue. Veuillez réessayer.')
  }
  revalidatePath('/courses')
  redirect('/courses')
}

export async function deleteCourse(id: string) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    await courseService.delete(userId, id)
  } catch {
    return { error: 'Impossible de supprimer cet élément.' }
  }
  revalidatePath('/courses')
  redirect('/courses')
}
