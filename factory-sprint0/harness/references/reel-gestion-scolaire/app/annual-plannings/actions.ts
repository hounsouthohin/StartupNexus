// AUTO-GÉNÉRÉ PAR dev_actions_generator.py — NE PAS MODIFIER
'use server'

import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import { revalidatePath } from 'next/cache'
import { ZodError } from 'zod'
import { annualPlanningService } from '@/lib/services/annual-planning.service'
import { CreateAnnualPlanningSchema, UpdateAnnualPlanningSchema } from '@/lib/schemas'

export async function createAnnualPlanning(formData: FormData) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    const validated = CreateAnnualPlanningSchema.parse(Object.fromEntries(formData) as Record<string, unknown>)
    await annualPlanningService.create(userId, validated)
  } catch (e) {
    if (e instanceof ZodError) throw new Error(e.errors.map(err => err.message).join(', '))
    throw new Error('Une erreur est survenue. Veuillez réessayer.')
  }
  revalidatePath('/annual-plannings')
  redirect('/annual-plannings')
}

export async function updateAnnualPlanning(id: string, formData: FormData) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    const validated = UpdateAnnualPlanningSchema.parse(Object.fromEntries(formData) as Record<string, unknown>)
    await annualPlanningService.update(userId, id, validated)
  } catch (e) {
    if (e instanceof ZodError) throw new Error(e.errors.map(err => err.message).join(', '))
    throw new Error('Une erreur est survenue. Veuillez réessayer.')
  }
  revalidatePath('/annual-plannings')
  redirect('/annual-plannings')
}

export async function deleteAnnualPlanning(id: string) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    await annualPlanningService.delete(userId, id)
  } catch {
    return { error: 'Impossible de supprimer cet élément.' }
  }
  revalidatePath('/annual-plannings')
  redirect('/annual-plannings')
}
