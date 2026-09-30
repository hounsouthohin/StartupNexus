// AUTO-GÉNÉRÉ PAR dev_actions_generator.py — NE PAS MODIFIER
'use server'

import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import { revalidatePath } from 'next/cache'
import { ZodError } from 'zod'
import { repairService } from '@/lib/services/repair.service'
import { CreateRepairSchema, UpdateRepairSchema } from '@/lib/schemas'
import { requireRole, hasRole } from '@/lib/auth-role'

export async function createRepair(formData: FormData) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  if (await hasRole('owner')) throw new Error('Création réservée aux clients — le rôle owner ne crée pas cette entité.')
  try {
    const validated = CreateRepairSchema.parse(Object.fromEntries(formData) as Record<string, unknown>)
    await repairService.create(userId, validated)
  } catch (e) {
    if (e instanceof ZodError) throw new Error(e.errors.map(err => err.message).join(', '))
    throw new Error('Une erreur est survenue. Veuillez réessayer.')
  }
  revalidatePath('/dashboard/repairs')
  redirect('/dashboard/repairs')
}

export async function updateRepair(id: string, formData: FormData) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    const validated = UpdateRepairSchema.parse(Object.fromEntries(formData) as Record<string, unknown>)
    await repairService.update(userId, id, validated)
  } catch (e) {
    if (e instanceof ZodError) throw new Error(e.errors.map(err => err.message).join(', '))
    throw new Error('Une erreur est survenue. Veuillez réessayer.')
  }
  revalidatePath('/dashboard/repairs')
  redirect('/dashboard/repairs')
}

export async function transitionRepair(id: string, newStatus: string, formData: FormData) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  await requireRole('owner')
  try {
    const data = UpdateRepairSchema.parse(Object.fromEntries(formData) as Record<string, unknown>)
    await repairService.transitionTo(userId, id, newStatus, data)
  } catch (e) {
    if (e instanceof ZodError) throw new Error(e.errors.map(err => err.message).join(', '))
    throw new Error('Une erreur est survenue. Veuillez réessayer.')
  }
  revalidatePath('/dashboard/repairs')
  redirect('/dashboard/repairs')
}

export async function deleteRepair(id: string) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    await repairService.delete(userId, id)
  } catch {
    return { error: 'Impossible de supprimer cet élément.' }
  }
  revalidatePath('/dashboard/repairs')
  redirect('/dashboard/repairs')
}
