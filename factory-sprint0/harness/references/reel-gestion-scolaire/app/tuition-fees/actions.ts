// AUTO-GÉNÉRÉ PAR dev_actions_generator.py — NE PAS MODIFIER
'use server'

import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import { revalidatePath } from 'next/cache'
import { ZodError } from 'zod'
import { tuitionFeeService } from '@/lib/services/tuition-fee.service'
import { CreateTuitionFeeSchema, UpdateTuitionFeeSchema } from '@/lib/schemas'

export async function createTuitionFee(formData: FormData) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    const validated = CreateTuitionFeeSchema.parse(Object.fromEntries(formData) as Record<string, unknown>)
    await tuitionFeeService.create(userId, validated)
  } catch (e) {
    if (e instanceof ZodError) throw new Error(e.errors.map(err => err.message).join(', '))
    throw new Error('Une erreur est survenue. Veuillez réessayer.')
  }
  revalidatePath('/tuition-fees')
  redirect('/tuition-fees')
}

export async function updateTuitionFee(id: string, formData: FormData) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    const validated = UpdateTuitionFeeSchema.parse(Object.fromEntries(formData) as Record<string, unknown>)
    await tuitionFeeService.update(userId, id, validated)
  } catch (e) {
    if (e instanceof ZodError) throw new Error(e.errors.map(err => err.message).join(', '))
    throw new Error('Une erreur est survenue. Veuillez réessayer.')
  }
  revalidatePath('/tuition-fees')
  redirect('/tuition-fees')
}

export async function deleteTuitionFee(id: string) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    await tuitionFeeService.delete(userId, id)
  } catch {
    return { error: 'Impossible de supprimer cet élément.' }
  }
  revalidatePath('/tuition-fees')
  redirect('/tuition-fees')
}
