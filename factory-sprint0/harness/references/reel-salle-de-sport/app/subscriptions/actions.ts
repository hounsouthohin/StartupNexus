// AUTO-GÉNÉRÉ PAR dev_actions_generator.py — NE PAS MODIFIER
'use server'

import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import { revalidatePath } from 'next/cache'
import { ZodError } from 'zod'
import { subscriptionService } from '@/lib/services/subscription.service'
import { CreateSubscriptionSchema, UpdateSubscriptionSchema } from '@/lib/schemas'
import { requireRole, hasRole } from '@/lib/auth-role'

export async function createSubscription(formData: FormData) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    const validated = CreateSubscriptionSchema.parse(Object.fromEntries(formData) as Record<string, unknown>)
    await subscriptionService.create(userId, validated)
  } catch (e) {
    if (e instanceof ZodError) throw new Error(e.errors.map(err => err.message).join(', '))
    throw new Error('Une erreur est survenue. Veuillez réessayer.')
  }
  revalidatePath('/subscriptions')
  redirect('/subscriptions')
}

export async function updateSubscription(id: string, formData: FormData) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    const validated = UpdateSubscriptionSchema.parse(Object.fromEntries(formData) as Record<string, unknown>)
    await subscriptionService.update(userId, id, validated)
  } catch (e) {
    if (e instanceof ZodError) throw new Error(e.errors.map(err => err.message).join(', '))
    throw new Error('Une erreur est survenue. Veuillez réessayer.')
  }
  revalidatePath('/subscriptions')
  redirect('/subscriptions')
}

export async function transitionSubscription(id: string, newStatus: string, formData: FormData) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  await requireRole('admin')
  try {
    const data = UpdateSubscriptionSchema.parse(Object.fromEntries(formData) as Record<string, unknown>)
    await subscriptionService.transitionTo(userId, id, newStatus, data)
  } catch (e) {
    if (e instanceof ZodError) throw new Error(e.errors.map(err => err.message).join(', '))
    throw new Error('Une erreur est survenue. Veuillez réessayer.')
  }
  revalidatePath('/subscriptions')
  redirect('/subscriptions')
}

export async function deleteSubscription(id: string) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    await subscriptionService.delete(userId, id)
  } catch {
    return { error: 'Impossible de supprimer cet élément.' }
  }
  revalidatePath('/subscriptions')
  redirect('/subscriptions')
}
