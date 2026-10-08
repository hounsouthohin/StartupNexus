// AUTO-GÉNÉRÉ PAR dev_actions_generator.py — NE PAS MODIFIER
'use server'

import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import { revalidatePath } from 'next/cache'
import { ZodError } from 'zod'
import { foreignExchangeService } from '@/lib/services/foreign-exchange.service'
import { CreateForeignExchangeSchema, UpdateForeignExchangeSchema } from '@/lib/schemas'

export async function createForeignExchange(formData: FormData) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    const validated = CreateForeignExchangeSchema.parse(Object.fromEntries(formData) as Record<string, unknown>)
    await foreignExchangeService.create(userId, validated)
  } catch (e) {
    if (e instanceof ZodError) throw new Error(e.errors.map(err => err.message).join(', '))
    throw new Error('Une erreur est survenue. Veuillez réessayer.')
  }
  revalidatePath('/foreign-exchanges')
  redirect('/foreign-exchanges')
}

export async function updateForeignExchange(id: string, formData: FormData) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    const validated = UpdateForeignExchangeSchema.parse(Object.fromEntries(formData) as Record<string, unknown>)
    await foreignExchangeService.update(userId, id, validated)
  } catch (e) {
    if (e instanceof ZodError) throw new Error(e.errors.map(err => err.message).join(', '))
    throw new Error('Une erreur est survenue. Veuillez réessayer.')
  }
  revalidatePath('/foreign-exchanges')
  redirect('/foreign-exchanges')
}

export async function deleteForeignExchange(id: string) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    await foreignExchangeService.delete(userId, id)
  } catch {
    return { error: 'Impossible de supprimer cet élément.' }
  }
  revalidatePath('/foreign-exchanges')
  redirect('/foreign-exchanges')
}
