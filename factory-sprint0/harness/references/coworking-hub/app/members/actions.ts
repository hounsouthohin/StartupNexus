// AUTO-GÉNÉRÉ PAR dev_actions_generator.py — NE PAS MODIFIER
'use server'

import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import { revalidatePath } from 'next/cache'
import { ZodError } from 'zod'
import { memberService } from '@/lib/services/member.service'
import { CreateMemberSchema, UpdateMemberSchema } from '@/lib/schemas'

export async function createMember(formData: FormData) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    const validated = CreateMemberSchema.parse(Object.fromEntries(formData) as Record<string, unknown>)
    await memberService.create(userId, validated)
  } catch (e) {
    if (e instanceof ZodError) throw new Error(e.errors.map(err => err.message).join(', '))
    throw new Error('Une erreur est survenue. Veuillez réessayer.')
  }
  revalidatePath('/members')
  redirect('/members')
}

export async function updateMember(id: string, formData: FormData) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    const validated = UpdateMemberSchema.parse(Object.fromEntries(formData) as Record<string, unknown>)
    await memberService.update(userId, id, validated)
  } catch (e) {
    if (e instanceof ZodError) throw new Error(e.errors.map(err => err.message).join(', '))
    throw new Error('Une erreur est survenue. Veuillez réessayer.')
  }
  revalidatePath('/members')
  redirect('/members')
}

export async function deleteMember(id: string) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    await memberService.delete(userId, id)
  } catch {
    return { error: 'Impossible de supprimer cet élément.' }
  }
  revalidatePath('/members')
  redirect('/members')
}
