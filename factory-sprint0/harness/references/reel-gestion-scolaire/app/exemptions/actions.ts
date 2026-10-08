// AUTO-GÉNÉRÉ PAR dev_actions_generator.py — NE PAS MODIFIER
'use server'

import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import { revalidatePath } from 'next/cache'
import { ZodError } from 'zod'
import { exemptionService } from '@/lib/services/exemption.service'
import { CreateExemptionSchema, UpdateExemptionSchema } from '@/lib/schemas'

export async function createExemption(formData: FormData) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    const validated = CreateExemptionSchema.parse(Object.fromEntries(formData) as Record<string, unknown>)
    await exemptionService.create(userId, validated)
  } catch (e) {
    if (e instanceof ZodError) throw new Error(e.errors.map(err => err.message).join(', '))
    throw new Error('Une erreur est survenue. Veuillez réessayer.')
  }
  revalidatePath('/exemptions')
  redirect('/exemptions')
}

export async function updateExemption(id: string, formData: FormData) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    const validated = UpdateExemptionSchema.parse(Object.fromEntries(formData) as Record<string, unknown>)
    await exemptionService.update(userId, id, validated)
  } catch (e) {
    if (e instanceof ZodError) throw new Error(e.errors.map(err => err.message).join(', '))
    throw new Error('Une erreur est survenue. Veuillez réessayer.')
  }
  revalidatePath('/exemptions')
  redirect('/exemptions')
}

export async function deleteExemption(id: string) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    await exemptionService.delete(userId, id)
  } catch {
    return { error: 'Impossible de supprimer cet élément.' }
  }
  revalidatePath('/exemptions')
  redirect('/exemptions')
}
