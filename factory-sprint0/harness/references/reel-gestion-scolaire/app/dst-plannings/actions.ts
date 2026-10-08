// AUTO-GÉNÉRÉ PAR dev_actions_generator.py — NE PAS MODIFIER
'use server'

import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import { revalidatePath } from 'next/cache'
import { ZodError } from 'zod'
import { dSTPlanningService } from '@/lib/services/d-s-t-planning.service'
import { CreateDSTPlanningSchema, UpdateDSTPlanningSchema } from '@/lib/schemas'

export async function createDSTPlanning(formData: FormData) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    const validated = CreateDSTPlanningSchema.parse(Object.fromEntries(formData) as Record<string, unknown>)
    await dSTPlanningService.create(userId, validated)
  } catch (e) {
    if (e instanceof ZodError) throw new Error(e.errors.map(err => err.message).join(', '))
    throw new Error('Une erreur est survenue. Veuillez réessayer.')
  }
  revalidatePath('/dst-plannings')
  redirect('/dst-plannings')
}

export async function updateDSTPlanning(id: string, formData: FormData) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    const validated = UpdateDSTPlanningSchema.parse(Object.fromEntries(formData) as Record<string, unknown>)
    await dSTPlanningService.update(userId, id, validated)
  } catch (e) {
    if (e instanceof ZodError) throw new Error(e.errors.map(err => err.message).join(', '))
    throw new Error('Une erreur est survenue. Veuillez réessayer.')
  }
  revalidatePath('/dst-plannings')
  redirect('/dst-plannings')
}

export async function deleteDSTPlanning(id: string) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    await dSTPlanningService.delete(userId, id)
  } catch {
    return { error: 'Impossible de supprimer cet élément.' }
  }
  revalidatePath('/dst-plannings')
  redirect('/dst-plannings')
}
