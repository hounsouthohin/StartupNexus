// AUTO-GÉNÉRÉ PAR dev_actions_generator.py — NE PAS MODIFIER
'use server'

import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import { revalidatePath } from 'next/cache'
import { ZodError } from 'zod'
import { sharedAgendaService } from '@/lib/services/shared-agenda.service'
import { CreateSharedAgendaSchema, UpdateSharedAgendaSchema } from '@/lib/schemas'

export async function createSharedAgenda(formData: FormData) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    const validated = CreateSharedAgendaSchema.parse(Object.fromEntries(formData) as Record<string, unknown>)
    await sharedAgendaService.create(userId, validated)
  } catch (e) {
    if (e instanceof ZodError) throw new Error(e.errors.map(err => err.message).join(', '))
    throw new Error('Une erreur est survenue. Veuillez réessayer.')
  }
  revalidatePath('/shared-agendas')
  redirect('/shared-agendas')
}

export async function updateSharedAgenda(id: string, formData: FormData) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    const validated = UpdateSharedAgendaSchema.parse(Object.fromEntries(formData) as Record<string, unknown>)
    await sharedAgendaService.update(userId, id, validated)
  } catch (e) {
    if (e instanceof ZodError) throw new Error(e.errors.map(err => err.message).join(', '))
    throw new Error('Une erreur est survenue. Veuillez réessayer.')
  }
  revalidatePath('/shared-agendas')
  redirect('/shared-agendas')
}

export async function deleteSharedAgenda(id: string) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    await sharedAgendaService.delete(userId, id)
  } catch {
    return { error: 'Impossible de supprimer cet élément.' }
  }
  revalidatePath('/shared-agendas')
  redirect('/shared-agendas')
}
