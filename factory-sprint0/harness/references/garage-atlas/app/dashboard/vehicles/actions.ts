// AUTO-GÉNÉRÉ PAR dev_actions_generator.py — NE PAS MODIFIER
'use server'

import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import { revalidatePath } from 'next/cache'
import { ZodError } from 'zod'
import { vehicleService } from '@/lib/services/vehicle.service'
import { CreateVehicleSchema, UpdateVehicleSchema } from '@/lib/schemas'

export async function createVehicle(formData: FormData) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    const validated = CreateVehicleSchema.parse(Object.fromEntries(formData) as Record<string, unknown>)
    await vehicleService.create(userId, validated)
  } catch (e) {
    if (e instanceof ZodError) throw new Error(e.errors.map(err => err.message).join(', '))
    throw new Error('Une erreur est survenue. Veuillez réessayer.')
  }
  revalidatePath('/dashboard/vehicles')
  redirect('/dashboard/vehicles')
}

export async function updateVehicle(id: string, formData: FormData) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    const validated = UpdateVehicleSchema.parse(Object.fromEntries(formData) as Record<string, unknown>)
    await vehicleService.update(userId, id, validated)
  } catch (e) {
    if (e instanceof ZodError) throw new Error(e.errors.map(err => err.message).join(', '))
    throw new Error('Une erreur est survenue. Veuillez réessayer.')
  }
  revalidatePath('/dashboard/vehicles')
  redirect('/dashboard/vehicles')
}

export async function deleteVehicle(id: string) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    await vehicleService.delete(userId, id)
  } catch {
    return { error: 'Impossible de supprimer cet élément.' }
  }
  revalidatePath('/dashboard/vehicles')
  redirect('/dashboard/vehicles')
}
