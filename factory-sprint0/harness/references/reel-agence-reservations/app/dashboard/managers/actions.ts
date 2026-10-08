// AUTO-GÉNÉRÉ PAR dev_actions_generator.py — NE PAS MODIFIER
'use server'

import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import { revalidatePath } from 'next/cache'
import { ZodError } from 'zod'
import { managerService } from '@/lib/services/manager.service'
import { CreateManagerSchema, UpdateManagerSchema } from '@/lib/schemas'
import { requireRole, hasRole } from '@/lib/auth-role'

export async function createManager(formData: FormData) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    const _raw = Object.fromEntries(formData) as Record<string, unknown>
    _raw.providerIds = formData.getAll('providerIds').map(String).filter(v => v.length > 0)
    const validated = CreateManagerSchema.parse(_raw)
    await managerService.create(userId, validated)
  } catch (e) {
    if (e instanceof ZodError) throw new Error(e.errors.map(err => err.message).join(', '))
    throw new Error('Une erreur est survenue. Veuillez réessayer.')
  }
  revalidatePath('/dashboard/managers')
  redirect('/dashboard/managers')
}

export async function updateManager(id: string, formData: FormData) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    const _raw = Object.fromEntries(formData) as Record<string, unknown>
    _raw.providerIds = formData.getAll('providerIds').map(String).filter(v => v.length > 0)
    const validated = UpdateManagerSchema.parse(_raw)
    await managerService.update(userId, id, validated)
  } catch (e) {
    if (e instanceof ZodError) throw new Error(e.errors.map(err => err.message).join(', '))
    throw new Error('Une erreur est survenue. Veuillez réessayer.')
  }
  revalidatePath('/dashboard/managers')
  redirect('/dashboard/managers')
}

export async function deleteManager(id: string) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    await managerService.delete(userId, id)
  } catch {
    return { error: 'Impossible de supprimer cet élément.' }
  }
  revalidatePath('/dashboard/managers')
  redirect('/dashboard/managers')
}
