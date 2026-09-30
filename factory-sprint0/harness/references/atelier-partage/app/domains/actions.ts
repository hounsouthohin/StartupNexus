// AUTO-GÉNÉRÉ PAR dev_actions_generator.py — NE PAS MODIFIER
'use server'

import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import { revalidatePath } from 'next/cache'
import { ZodError } from 'zod'
import { domainService } from '@/lib/services/domain.service'
import { CreateDomainSchema, UpdateDomainSchema } from '@/lib/schemas'

export async function createDomain(formData: FormData) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    const _raw = Object.fromEntries(formData) as Record<string, unknown>
    _raw.workshopIds = formData.getAll('workshopIds').map(String).filter(v => v.length > 0)
    const validated = CreateDomainSchema.parse(_raw)
    await domainService.create(userId, validated)
  } catch (e) {
    if (e instanceof ZodError) throw new Error(e.errors.map(err => err.message).join(', '))
    throw new Error('Une erreur est survenue. Veuillez réessayer.')
  }
  revalidatePath('/domains')
  redirect('/domains')
}

export async function updateDomain(id: string, formData: FormData) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    const _raw = Object.fromEntries(formData) as Record<string, unknown>
    _raw.workshopIds = formData.getAll('workshopIds').map(String).filter(v => v.length > 0)
    const validated = UpdateDomainSchema.parse(_raw)
    await domainService.update(userId, id, validated)
  } catch (e) {
    if (e instanceof ZodError) throw new Error(e.errors.map(err => err.message).join(', '))
    throw new Error('Une erreur est survenue. Veuillez réessayer.')
  }
  revalidatePath('/domains')
  redirect('/domains')
}

export async function deleteDomain(id: string) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    await domainService.delete(userId, id)
  } catch {
    return { error: 'Impossible de supprimer cet élément.' }
  }
  revalidatePath('/domains')
  redirect('/domains')
}
