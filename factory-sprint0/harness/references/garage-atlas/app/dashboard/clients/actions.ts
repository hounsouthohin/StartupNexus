// AUTO-GÉNÉRÉ PAR dev_actions_generator.py — NE PAS MODIFIER
'use server'

import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import { revalidatePath } from 'next/cache'
import { ZodError } from 'zod'
import { clientService } from '@/lib/services/client.service'
import { CreateClientSchema, UpdateClientSchema } from '@/lib/schemas'

export async function createClient(formData: FormData) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    const validated = CreateClientSchema.parse(Object.fromEntries(formData) as Record<string, unknown>)
    await clientService.create(userId, validated)
  } catch (e) {
    if (e instanceof ZodError) throw new Error(e.errors.map(err => err.message).join(', '))
    throw new Error('Une erreur est survenue. Veuillez réessayer.')
  }
  revalidatePath('/dashboard/clients')
  redirect('/dashboard/clients')
}

export async function updateClient(id: string, formData: FormData) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    const validated = UpdateClientSchema.parse(Object.fromEntries(formData) as Record<string, unknown>)
    await clientService.update(userId, id, validated)
  } catch (e) {
    if (e instanceof ZodError) throw new Error(e.errors.map(err => err.message).join(', '))
    throw new Error('Une erreur est survenue. Veuillez réessayer.')
  }
  revalidatePath('/dashboard/clients')
  redirect('/dashboard/clients')
}

export async function deleteClient(id: string) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    await clientService.delete(userId, id)
  } catch {
    return { error: 'Impossible de supprimer cet élément.' }
  }
  revalidatePath('/dashboard/clients')
  redirect('/dashboard/clients')
}
