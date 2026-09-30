// AUTO-GÉNÉRÉ PAR dev_actions_generator.py — NE PAS MODIFIER
'use server'

import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import { revalidatePath } from 'next/cache'
import { ZodError } from 'zod'
import { slotService } from '@/lib/services/slot.service'
import { CreateSlotSchema, UpdateSlotSchema } from '@/lib/schemas'

export async function createSlot(formData: FormData) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    const validated = CreateSlotSchema.parse(Object.fromEntries(formData) as Record<string, unknown>)
    await slotService.create(userId, validated)
  } catch (e) {
    if (e instanceof ZodError) throw new Error(e.errors.map(err => err.message).join(', '))
    throw new Error('Une erreur est survenue. Veuillez réessayer.')
  }
  revalidatePath('/slots')
  redirect('/slots')
}

export async function updateSlot(id: string, formData: FormData) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    const validated = UpdateSlotSchema.parse(Object.fromEntries(formData) as Record<string, unknown>)
    await slotService.update(userId, id, validated)
  } catch (e) {
    if (e instanceof ZodError) throw new Error(e.errors.map(err => err.message).join(', '))
    throw new Error('Une erreur est survenue. Veuillez réessayer.')
  }
  revalidatePath('/slots')
  redirect('/slots')
}

export async function deleteSlot(id: string) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    await slotService.delete(userId, id)
  } catch {
    return { error: 'Impossible de supprimer cet élément.' }
  }
  revalidatePath('/slots')
  redirect('/slots')
}
