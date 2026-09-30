// AUTO-GÉNÉRÉ PAR dev_actions_generator.py — NE PAS MODIFIER
'use server'

import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import { revalidatePath } from 'next/cache'
import { ZodError } from 'zod'
import { workshopService } from '@/lib/services/workshop.service'
import { CreateWorkshopSchema, UpdateWorkshopSchema } from '@/lib/schemas'

export async function createWorkshop(formData: FormData) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    const _raw = Object.fromEntries(formData) as Record<string, unknown>
    _raw.domainIds = formData.getAll('domainIds').map(String).filter(v => v.length > 0)
    const validated = CreateWorkshopSchema.parse(_raw)
    await workshopService.create(userId, validated)
  } catch (e) {
    if (e instanceof ZodError) throw new Error(e.errors.map(err => err.message).join(', '))
    throw new Error('Une erreur est survenue. Veuillez réessayer.')
  }
  revalidatePath('/dashboard/workshops')
  redirect('/dashboard/workshops')
}

export async function updateWorkshop(id: string, formData: FormData) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    const _raw = Object.fromEntries(formData) as Record<string, unknown>
    _raw.domainIds = formData.getAll('domainIds').map(String).filter(v => v.length > 0)
    const validated = UpdateWorkshopSchema.parse(_raw)
    await workshopService.update(userId, id, validated)
  } catch (e) {
    if (e instanceof ZodError) throw new Error(e.errors.map(err => err.message).join(', '))
    throw new Error('Une erreur est survenue. Veuillez réessayer.')
  }
  revalidatePath('/dashboard/workshops')
  redirect('/dashboard/workshops')
}

export async function deleteWorkshop(id: string) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    await workshopService.delete(userId, id)
  } catch {
    return { error: 'Impossible de supprimer cet élément.' }
  }
  revalidatePath('/dashboard/workshops')
  redirect('/dashboard/workshops')
}
