// AUTO-GÉNÉRÉ PAR dev_actions_generator.py — NE PAS MODIFIER
'use server'

import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import { revalidatePath } from 'next/cache'
import { ZodError } from 'zod'
import { borrowingService } from '@/lib/services/borrowing.service'
import { CreateBorrowingSchema, UpdateBorrowingSchema } from '@/lib/schemas'
import { requireRole, hasRole } from '@/lib/auth-role'

export async function createBorrowing(formData: FormData) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  if (await hasRole('librarian')) throw new Error('Création réservée aux members — le rôle librarian ne crée pas cette entité.')
  try {
    const validated = CreateBorrowingSchema.parse(Object.fromEntries(formData) as Record<string, unknown>)
    await borrowingService.create(userId, validated)
  } catch (e) {
    if (e instanceof ZodError) throw new Error(e.errors.map(err => err.message).join(', '))
    throw new Error('Une erreur est survenue. Veuillez réessayer.')
  }
  revalidatePath('/dashboard/borrowings')
  redirect('/dashboard/borrowings')
}

export async function updateBorrowing(id: string, formData: FormData) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    const validated = UpdateBorrowingSchema.parse(Object.fromEntries(formData) as Record<string, unknown>)
    await borrowingService.update(userId, id, validated)
  } catch (e) {
    if (e instanceof ZodError) throw new Error(e.errors.map(err => err.message).join(', '))
    throw new Error('Une erreur est survenue. Veuillez réessayer.')
  }
  revalidatePath('/dashboard/borrowings')
  redirect('/dashboard/borrowings')
}

export async function transitionBorrowing(id: string, newStatus: string, formData: FormData) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  await requireRole('librarian')
  try {
    const data = UpdateBorrowingSchema.parse(Object.fromEntries(formData) as Record<string, unknown>)
    await borrowingService.transitionTo(userId, id, newStatus, data)
  } catch (e) {
    if (e instanceof ZodError) throw new Error(e.errors.map(err => err.message).join(', '))
    throw new Error('Une erreur est survenue. Veuillez réessayer.')
  }
  revalidatePath('/dashboard/borrowings')
  redirect('/dashboard/borrowings')
}

export async function deleteBorrowing(id: string) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    await borrowingService.delete(userId, id)
  } catch {
    return { error: 'Impossible de supprimer cet élément.' }
  }
  revalidatePath('/dashboard/borrowings')
  redirect('/dashboard/borrowings')
}
