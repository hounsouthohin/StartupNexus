// AUTO-GÉNÉRÉ PAR dev_actions_generator.py — NE PAS MODIFIER
'use server'

import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import { revalidatePath } from 'next/cache'
import { ZodError } from 'zod'
import { sanctionService } from '@/lib/services/sanction.service'
import { CreateSanctionSchema, UpdateSanctionSchema } from '@/lib/schemas'

export async function createSanction(formData: FormData) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    const validated = CreateSanctionSchema.parse(Object.fromEntries(formData) as Record<string, unknown>)
    await sanctionService.create(userId, validated)
  } catch (e) {
    if (e instanceof ZodError) throw new Error(e.errors.map(err => err.message).join(', '))
    throw new Error('Une erreur est survenue. Veuillez réessayer.')
  }
  revalidatePath('/sanctions')
  redirect('/sanctions')
}

export async function updateSanction(id: string, formData: FormData) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    const validated = UpdateSanctionSchema.parse(Object.fromEntries(formData) as Record<string, unknown>)
    await sanctionService.update(userId, id, validated)
  } catch (e) {
    if (e instanceof ZodError) throw new Error(e.errors.map(err => err.message).join(', '))
    throw new Error('Une erreur est survenue. Veuillez réessayer.')
  }
  revalidatePath('/sanctions')
  redirect('/sanctions')
}

export async function deleteSanction(id: string) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    await sanctionService.delete(userId, id)
  } catch {
    return { error: 'Impossible de supprimer cet élément.' }
  }
  revalidatePath('/sanctions')
  redirect('/sanctions')
}
