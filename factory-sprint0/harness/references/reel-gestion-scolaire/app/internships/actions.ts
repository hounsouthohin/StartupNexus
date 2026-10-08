// AUTO-GÉNÉRÉ PAR dev_actions_generator.py — NE PAS MODIFIER
'use server'

import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import { revalidatePath } from 'next/cache'
import { ZodError } from 'zod'
import { internshipService } from '@/lib/services/internship.service'
import { CreateInternshipSchema, UpdateInternshipSchema } from '@/lib/schemas'

export async function createInternship(formData: FormData) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    const validated = CreateInternshipSchema.parse(Object.fromEntries(formData) as Record<string, unknown>)
    await internshipService.create(userId, validated)
  } catch (e) {
    if (e instanceof ZodError) throw new Error(e.errors.map(err => err.message).join(', '))
    throw new Error('Une erreur est survenue. Veuillez réessayer.')
  }
  revalidatePath('/internships')
  redirect('/internships')
}

export async function updateInternship(id: string, formData: FormData) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    const validated = UpdateInternshipSchema.parse(Object.fromEntries(formData) as Record<string, unknown>)
    await internshipService.update(userId, id, validated)
  } catch (e) {
    if (e instanceof ZodError) throw new Error(e.errors.map(err => err.message).join(', '))
    throw new Error('Une erreur est survenue. Veuillez réessayer.')
  }
  revalidatePath('/internships')
  redirect('/internships')
}

export async function deleteInternship(id: string) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    await internshipService.delete(userId, id)
  } catch {
    return { error: 'Impossible de supprimer cet élément.' }
  }
  revalidatePath('/internships')
  redirect('/internships')
}
