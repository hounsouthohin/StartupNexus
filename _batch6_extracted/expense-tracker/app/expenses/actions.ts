// AUTO-GÉNÉRÉ PAR dev_actions_generator.py — NE PAS MODIFIER
'use server'

import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import { revalidatePath } from 'next/cache'
import { expenseService } from '@/lib/services/expense.service'
import { CreateExpenseSchema, UpdateExpenseSchema } from '@/lib/schemas'

export async function createExpense(formData: FormData) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const validated = CreateExpenseSchema.parse(Object.fromEntries(formData) as Record<string, unknown>)
  await expenseService.create(userId, validated)
  revalidatePath('/expenses')
  redirect('/expenses')
}

export async function updateExpense(id: string, formData: FormData) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const validated = UpdateExpenseSchema.parse(Object.fromEntries(formData) as Record<string, unknown>)
  await expenseService.update(userId, id, validated)
  revalidatePath('/expenses')
  redirect('/expenses')
}

export async function deleteExpense(id: string) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  await expenseService.delete(userId, id)
  revalidatePath('/expenses')
  redirect('/expenses')
}
