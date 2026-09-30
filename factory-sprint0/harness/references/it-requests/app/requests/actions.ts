// AUTO-GÉNÉRÉ PAR dev_actions_generator.py — NE PAS MODIFIER
'use server'

import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import { revalidatePath } from 'next/cache'
import { ZodError } from 'zod'
import { requestService } from '@/lib/services/request.service'
import { CreateRequestSchema, UpdateRequestSchema } from '@/lib/schemas'
import { requireRole, hasRole } from '@/lib/auth-role'

export async function createRequest(formData: FormData) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  if (await hasRole('admin')) throw new Error('Création réservée aux employees — le rôle admin ne crée pas cette entité.')
  try {
    const validated = CreateRequestSchema.parse(Object.fromEntries(formData) as Record<string, unknown>)
    await requestService.create(userId, validated)
  } catch (e) {
    if (e instanceof ZodError) throw new Error(e.errors.map(err => err.message).join(', '))
    throw new Error('Une erreur est survenue. Veuillez réessayer.')
  }
  revalidatePath('/requests')
  redirect('/requests')
}

export async function updateRequest(id: string, formData: FormData) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    const validated = UpdateRequestSchema.parse(Object.fromEntries(formData) as Record<string, unknown>)
    await requestService.update(userId, id, validated)
  } catch (e) {
    if (e instanceof ZodError) throw new Error(e.errors.map(err => err.message).join(', '))
    throw new Error('Une erreur est survenue. Veuillez réessayer.')
  }
  revalidatePath('/requests')
  redirect('/requests')
}

export async function transitionRequest(id: string, newStatus: string, formData: FormData) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  await requireRole('admin')
  try {
    const data = UpdateRequestSchema.parse(Object.fromEntries(formData) as Record<string, unknown>)
    await requestService.transitionTo(userId, id, newStatus, data)
  } catch (e) {
    if (e instanceof ZodError) throw new Error(e.errors.map(err => err.message).join(', '))
    throw new Error('Une erreur est survenue. Veuillez réessayer.')
  }
  revalidatePath('/requests')
  redirect('/requests')
}

export async function deleteRequest(id: string) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    await requestService.delete(userId, id)
  } catch {
    return { error: 'Impossible de supprimer cet élément.' }
  }
  revalidatePath('/requests')
  redirect('/requests')
}
