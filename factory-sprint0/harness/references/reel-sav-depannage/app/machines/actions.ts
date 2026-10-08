// AUTO-GÉNÉRÉ PAR dev_actions_generator.py — NE PAS MODIFIER
'use server'

import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import { revalidatePath } from 'next/cache'
import { ZodError } from 'zod'
import { machineService } from '@/lib/services/machine.service'
import { CreateMachineSchema, UpdateMachineSchema } from '@/lib/schemas'

export async function createMachine(formData: FormData) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    const validated = CreateMachineSchema.parse(Object.fromEntries(formData) as Record<string, unknown>)
    await machineService.create(userId, validated)
  } catch (e) {
    if (e instanceof ZodError) throw new Error(e.errors.map(err => err.message).join(', '))
    throw new Error('Une erreur est survenue. Veuillez réessayer.')
  }
  revalidatePath('/machines')
  redirect('/machines')
}

export async function updateMachine(id: string, formData: FormData) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    const validated = UpdateMachineSchema.parse(Object.fromEntries(formData) as Record<string, unknown>)
    await machineService.update(userId, id, validated)
  } catch (e) {
    if (e instanceof ZodError) throw new Error(e.errors.map(err => err.message).join(', '))
    throw new Error('Une erreur est survenue. Veuillez réessayer.')
  }
  revalidatePath('/machines')
  redirect('/machines')
}

export async function deleteMachine(id: string) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    await machineService.delete(userId, id)
  } catch {
    return { error: 'Impossible de supprimer cet élément.' }
  }
  revalidatePath('/machines')
  redirect('/machines')
}
