// AUTO-GÉNÉRÉ PAR dev_actions_generator.py — NE PAS MODIFIER
'use server'

import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import { revalidatePath } from 'next/cache'
import { ZodError } from 'zod'
import { expenseReportService } from '@/lib/services/expense-report.service'
import { CreateExpenseReportSchema, UpdateExpenseReportSchema } from '@/lib/schemas'

export async function createExpenseReport(formData: FormData) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    const validated = CreateExpenseReportSchema.parse(Object.fromEntries(formData) as Record<string, unknown>)
    await expenseReportService.create(userId, validated)
  } catch (e) {
    if (e instanceof ZodError) throw new Error(e.errors.map(err => err.message).join(', '))
    throw new Error('Une erreur est survenue. Veuillez réessayer.')
  }
  revalidatePath('/expense-reports')
  redirect('/expense-reports')
}

export async function updateExpenseReport(id: string, formData: FormData) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    const validated = UpdateExpenseReportSchema.parse(Object.fromEntries(formData) as Record<string, unknown>)
    await expenseReportService.update(userId, id, validated)
  } catch (e) {
    if (e instanceof ZodError) throw new Error(e.errors.map(err => err.message).join(', '))
    throw new Error('Une erreur est survenue. Veuillez réessayer.')
  }
  revalidatePath('/expense-reports')
  redirect('/expense-reports')
}

export async function transitionExpenseReport(id: string, newStatus: string, formData: FormData) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    const data = UpdateExpenseReportSchema.parse(Object.fromEntries(formData) as Record<string, unknown>)
    await expenseReportService.transitionTo(userId, id, newStatus, data)
  } catch (e) {
    if (e instanceof ZodError) throw new Error(e.errors.map(err => err.message).join(', '))
    throw new Error('Une erreur est survenue. Veuillez réessayer.')
  }
  revalidatePath('/expense-reports')
  redirect('/expense-reports')
}

export async function deleteExpenseReport(id: string) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    await expenseReportService.delete(userId, id)
  } catch {
    return { error: 'Impossible de supprimer cet élément.' }
  }
  revalidatePath('/expense-reports')
  redirect('/expense-reports')
}
