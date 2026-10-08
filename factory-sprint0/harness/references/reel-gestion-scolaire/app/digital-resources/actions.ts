// AUTO-GÉNÉRÉ PAR dev_actions_generator.py — NE PAS MODIFIER
'use server'

import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import { revalidatePath } from 'next/cache'
import { ZodError } from 'zod'
import { digitalResourceService } from '@/lib/services/digital-resource.service'
import { CreateDigitalResourceSchema, UpdateDigitalResourceSchema } from '@/lib/schemas'

export async function createDigitalResource(formData: FormData) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    const validated = CreateDigitalResourceSchema.parse(Object.fromEntries(formData) as Record<string, unknown>)
    await digitalResourceService.create(userId, validated)
  } catch (e) {
    if (e instanceof ZodError) throw new Error(e.errors.map(err => err.message).join(', '))
    throw new Error('Une erreur est survenue. Veuillez réessayer.')
  }
  revalidatePath('/digital-resources')
  redirect('/digital-resources')
}

export async function updateDigitalResource(id: string, formData: FormData) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    const validated = UpdateDigitalResourceSchema.parse(Object.fromEntries(formData) as Record<string, unknown>)
    await digitalResourceService.update(userId, id, validated)
  } catch (e) {
    if (e instanceof ZodError) throw new Error(e.errors.map(err => err.message).join(', '))
    throw new Error('Une erreur est survenue. Veuillez réessayer.')
  }
  revalidatePath('/digital-resources')
  redirect('/digital-resources')
}

export async function deleteDigitalResource(id: string) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    await digitalResourceService.delete(userId, id)
  } catch {
    return { error: 'Impossible de supprimer cet élément.' }
  }
  revalidatePath('/digital-resources')
  redirect('/digital-resources')
}
