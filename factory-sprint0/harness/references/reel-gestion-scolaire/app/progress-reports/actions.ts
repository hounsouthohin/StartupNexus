// AUTO-GÉNÉRÉ PAR dev_actions_generator.py — NE PAS MODIFIER
'use server'

import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import { revalidatePath } from 'next/cache'
import { ZodError } from 'zod'
import { progressReportService } from '@/lib/services/progress-report.service'
import { CreateProgressReportSchema, UpdateProgressReportSchema } from '@/lib/schemas'

export async function createProgressReport(formData: FormData) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    const validated = CreateProgressReportSchema.parse(Object.fromEntries(formData) as Record<string, unknown>)
    await progressReportService.create(userId, validated)
  } catch (e) {
    if (e instanceof ZodError) throw new Error(e.errors.map(err => err.message).join(', '))
    throw new Error('Une erreur est survenue. Veuillez réessayer.')
  }
  revalidatePath('/progress-reports')
  redirect('/progress-reports')
}

export async function updateProgressReport(id: string, formData: FormData) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    const validated = UpdateProgressReportSchema.parse(Object.fromEntries(formData) as Record<string, unknown>)
    await progressReportService.update(userId, id, validated)
  } catch (e) {
    if (e instanceof ZodError) throw new Error(e.errors.map(err => err.message).join(', '))
    throw new Error('Une erreur est survenue. Veuillez réessayer.')
  }
  revalidatePath('/progress-reports')
  redirect('/progress-reports')
}

export async function deleteProgressReport(id: string) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    await progressReportService.delete(userId, id)
  } catch {
    return { error: 'Impossible de supprimer cet élément.' }
  }
  revalidatePath('/progress-reports')
  redirect('/progress-reports')
}
