// AUTO-GÉNÉRÉ PAR dev_actions_generator.py — NE PAS MODIFIER
'use server'

import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import { revalidatePath } from 'next/cache'
import { ZodError } from 'zod'
import { alertService } from '@/lib/services/alert.service'
import { CreateAlertSchema, UpdateAlertSchema } from '@/lib/schemas'

export async function createAlert(formData: FormData) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    const validated = CreateAlertSchema.parse(Object.fromEntries(formData) as Record<string, unknown>)
    await alertService.create(userId, validated)
  } catch (e) {
    if (e instanceof ZodError) throw new Error(e.errors.map(err => err.message).join(', '))
    throw new Error('Une erreur est survenue. Veuillez réessayer.')
  }
  revalidatePath('/dashboard/alerts')
  redirect('/dashboard/alerts')
}

export async function updateAlert(id: string, formData: FormData) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    const validated = UpdateAlertSchema.parse(Object.fromEntries(formData) as Record<string, unknown>)
    await alertService.update(userId, id, validated)
  } catch (e) {
    if (e instanceof ZodError) throw new Error(e.errors.map(err => err.message).join(', '))
    throw new Error('Une erreur est survenue. Veuillez réessayer.')
  }
  revalidatePath('/dashboard/alerts')
  redirect('/dashboard/alerts')
}

export async function deleteAlert(id: string) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    await alertService.delete(userId, id)
  } catch {
    return { error: 'Impossible de supprimer cet élément.' }
  }
  revalidatePath('/dashboard/alerts')
  redirect('/dashboard/alerts')
}
