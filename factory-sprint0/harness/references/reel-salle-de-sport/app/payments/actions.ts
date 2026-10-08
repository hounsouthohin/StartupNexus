// AUTO-GÉNÉRÉ PAR dev_actions_generator.py — NE PAS MODIFIER
'use server'

import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import { revalidatePath } from 'next/cache'
import { ZodError } from 'zod'
import { paymentService } from '@/lib/services/payment.service'
import { CreatePaymentSchema, UpdatePaymentSchema } from '@/lib/schemas'

export async function createPayment(formData: FormData) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    const validated = CreatePaymentSchema.parse(Object.fromEntries(formData) as Record<string, unknown>)
    await paymentService.create(userId, validated)
  } catch (e) {
    if (e instanceof ZodError) throw new Error(e.errors.map(err => err.message).join(', '))
    throw new Error('Une erreur est survenue. Veuillez réessayer.')
  }
  revalidatePath('/payments')
  redirect('/payments')
}

export async function updatePayment(id: string, formData: FormData) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    const validated = UpdatePaymentSchema.parse(Object.fromEntries(formData) as Record<string, unknown>)
    await paymentService.update(userId, id, validated)
  } catch (e) {
    if (e instanceof ZodError) throw new Error(e.errors.map(err => err.message).join(', '))
    throw new Error('Une erreur est survenue. Veuillez réessayer.')
  }
  revalidatePath('/payments')
  redirect('/payments')
}

export async function deletePayment(id: string) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    await paymentService.delete(userId, id)
  } catch {
    return { error: 'Impossible de supprimer cet élément.' }
  }
  revalidatePath('/payments')
  redirect('/payments')
}
