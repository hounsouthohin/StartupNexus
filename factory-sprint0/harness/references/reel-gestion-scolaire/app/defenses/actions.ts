// AUTO-GÉNÉRÉ PAR dev_actions_generator.py — NE PAS MODIFIER
'use server'

import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import { revalidatePath } from 'next/cache'
import { ZodError } from 'zod'
import { defenseService } from '@/lib/services/defense.service'
import { CreateDefenseSchema, UpdateDefenseSchema } from '@/lib/schemas'

export async function createDefense(formData: FormData) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    const validated = CreateDefenseSchema.parse(Object.fromEntries(formData) as Record<string, unknown>)
    await defenseService.create(userId, validated)
  } catch (e) {
    if (e instanceof ZodError) throw new Error(e.errors.map(err => err.message).join(', '))
    throw new Error('Une erreur est survenue. Veuillez réessayer.')
  }
  revalidatePath('/defenses')
  redirect('/defenses')
}

export async function updateDefense(id: string, formData: FormData) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    const validated = UpdateDefenseSchema.parse(Object.fromEntries(formData) as Record<string, unknown>)
    await defenseService.update(userId, id, validated)
  } catch (e) {
    if (e instanceof ZodError) throw new Error(e.errors.map(err => err.message).join(', '))
    throw new Error('Une erreur est survenue. Veuillez réessayer.')
  }
  revalidatePath('/defenses')
  redirect('/defenses')
}

export async function deleteDefense(id: string) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    await defenseService.delete(userId, id)
  } catch {
    return { error: 'Impossible de supprimer cet élément.' }
  }
  revalidatePath('/defenses')
  redirect('/defenses')
}
