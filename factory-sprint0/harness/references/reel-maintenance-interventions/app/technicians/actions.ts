// AUTO-GÉNÉRÉ PAR dev_actions_generator.py — NE PAS MODIFIER
'use server'

import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import { revalidatePath } from 'next/cache'
import { ZodError } from 'zod'
import { technicianService } from '@/lib/services/technician.service'
import { CreateTechnicianSchema, UpdateTechnicianSchema } from '@/lib/schemas'

export async function createTechnician(formData: FormData) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    const validated = CreateTechnicianSchema.parse(Object.fromEntries(formData) as Record<string, unknown>)
    await technicianService.create(userId, validated)
  } catch (e) {
    if (e instanceof ZodError) throw new Error(e.errors.map(err => err.message).join(', '))
    throw new Error('Une erreur est survenue. Veuillez réessayer.')
  }
  revalidatePath('/technicians')
  redirect('/technicians')
}

export async function updateTechnician(id: string, formData: FormData) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    const validated = UpdateTechnicianSchema.parse(Object.fromEntries(formData) as Record<string, unknown>)
    await technicianService.update(userId, id, validated)
  } catch (e) {
    if (e instanceof ZodError) throw new Error(e.errors.map(err => err.message).join(', '))
    throw new Error('Une erreur est survenue. Veuillez réessayer.')
  }
  revalidatePath('/technicians')
  redirect('/technicians')
}

export async function deleteTechnician(id: string) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    await technicianService.delete(userId, id)
  } catch {
    return { error: 'Impossible de supprimer cet élément.' }
  }
  revalidatePath('/technicians')
  redirect('/technicians')
}
