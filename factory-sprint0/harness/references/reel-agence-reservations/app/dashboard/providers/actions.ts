// AUTO-GÉNÉRÉ PAR dev_actions_generator.py — NE PAS MODIFIER
'use server'

import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import { revalidatePath } from 'next/cache'
import { ZodError } from 'zod'
import { providerService } from '@/lib/services/provider.service'
import { CreateProviderSchema, UpdateProviderSchema } from '@/lib/schemas'
import { requireRole, hasRole } from '@/lib/auth-role'

export async function createProvider(formData: FormData) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    const _raw = Object.fromEntries(formData) as Record<string, unknown>
    _raw.managerIds = formData.getAll('managerIds').map(String).filter(v => v.length > 0)
    const validated = CreateProviderSchema.parse(_raw)
    await providerService.create(userId, validated)
  } catch (e) {
    if (e instanceof ZodError) throw new Error(e.errors.map(err => err.message).join(', '))
    throw new Error('Une erreur est survenue. Veuillez réessayer.')
  }
  revalidatePath('/dashboard/providers')
  redirect('/dashboard/providers')
}

export async function updateProvider(id: string, formData: FormData) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    const _raw = Object.fromEntries(formData) as Record<string, unknown>
    _raw.managerIds = formData.getAll('managerIds').map(String).filter(v => v.length > 0)
    const validated = UpdateProviderSchema.parse(_raw)
    await providerService.update(userId, id, validated)
  } catch (e) {
    if (e instanceof ZodError) throw new Error(e.errors.map(err => err.message).join(', '))
    throw new Error('Une erreur est survenue. Veuillez réessayer.')
  }
  revalidatePath('/dashboard/providers')
  redirect('/dashboard/providers')
}

export async function deleteProvider(id: string) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    await providerService.delete(userId, id)
  } catch {
    return { error: 'Impossible de supprimer cet élément.' }
  }
  revalidatePath('/dashboard/providers')
  redirect('/dashboard/providers')
}
