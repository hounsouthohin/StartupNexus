// AUTO-GÉNÉRÉ PAR dev_actions_generator.py — NE PAS MODIFIER
'use server'

import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import { revalidatePath } from 'next/cache'
import { ZodError } from 'zod'
import { disciplineService } from '@/lib/services/discipline.service'
import { CreateDisciplineSchema, UpdateDisciplineSchema } from '@/lib/schemas'

export async function createDiscipline(formData: FormData) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    const validated = CreateDisciplineSchema.parse(Object.fromEntries(formData) as Record<string, unknown>)
    await disciplineService.create(userId, validated)
  } catch (e) {
    if (e instanceof ZodError) throw new Error(e.errors.map(err => err.message).join(', '))
    throw new Error('Une erreur est survenue. Veuillez réessayer.')
  }
  revalidatePath('/disciplines')
  redirect('/disciplines')
}

export async function updateDiscipline(id: string, formData: FormData) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    const validated = UpdateDisciplineSchema.parse(Object.fromEntries(formData) as Record<string, unknown>)
    await disciplineService.update(userId, id, validated)
  } catch (e) {
    if (e instanceof ZodError) throw new Error(e.errors.map(err => err.message).join(', '))
    throw new Error('Une erreur est survenue. Veuillez réessayer.')
  }
  revalidatePath('/disciplines')
  redirect('/disciplines')
}

export async function deleteDiscipline(id: string) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    await disciplineService.delete(userId, id)
  } catch {
    return { error: 'Impossible de supprimer cet élément.' }
  }
  revalidatePath('/disciplines')
  redirect('/disciplines')
}
