// AUTO-GÉNÉRÉ PAR dev_actions_generator.py — NE PAS MODIFIER
'use server'

import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import { revalidatePath } from 'next/cache'
import { ZodError } from 'zod'
import { interventionService } from '@/lib/services/intervention.service'
import { CreateInterventionSchema, UpdateInterventionSchema } from '@/lib/schemas'
import { requireRole, hasRole } from '@/lib/auth-role'

export async function createIntervention(formData: FormData) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  await requireRole('admin')
  try {
    const validated = CreateInterventionSchema.parse(Object.fromEntries(formData) as Record<string, unknown>)
    await interventionService.create(userId, validated)
  } catch (e) {
    if (e instanceof ZodError) throw new Error(e.errors.map(err => err.message).join(', '))
    throw new Error('Une erreur est survenue. Veuillez réessayer.')
  }
  revalidatePath('/interventions')
  redirect('/interventions')
}

export async function updateIntervention(id: string, formData: FormData) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    const validated = UpdateInterventionSchema.parse(Object.fromEntries(formData) as Record<string, unknown>)
    await interventionService.update(userId, id, validated)
  } catch (e) {
    if (e instanceof ZodError) throw new Error(e.errors.map(err => err.message).join(', '))
    throw new Error('Une erreur est survenue. Veuillez réessayer.')
  }
  revalidatePath('/interventions')
  redirect('/interventions')
}

export async function transitionIntervention(id: string, newStatus: string, formData: FormData) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  await requireRole('admin')
  try {
    const data = UpdateInterventionSchema.parse(Object.fromEntries(formData) as Record<string, unknown>)
    await interventionService.transitionTo(userId, id, newStatus, data)
  } catch (e) {
    if (e instanceof ZodError) throw new Error(e.errors.map(err => err.message).join(', '))
    throw new Error('Une erreur est survenue. Veuillez réessayer.')
  }
  revalidatePath('/interventions')
  redirect('/interventions')
}

export async function deleteIntervention(id: string) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    await interventionService.delete(userId, id)
  } catch {
    return { error: 'Impossible de supprimer cet élément.' }
  }
  revalidatePath('/interventions')
  redirect('/interventions')
}
