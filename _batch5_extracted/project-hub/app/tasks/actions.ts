// AUTO-GÉNÉRÉ PAR dev_actions_generator.py — NE PAS MODIFIER
'use server'

import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import { revalidatePath } from 'next/cache'
import { taskService } from '@/lib/services/task.service'
import { CreateTaskSchema, UpdateTaskSchema } from '@/lib/schemas'

export async function createTask(formData: FormData) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const validated = CreateTaskSchema.parse(Object.fromEntries(formData) as Record<string, unknown>)
  await taskService.create(userId, validated)
  revalidatePath('/tasks')
  redirect('/tasks')
}

export async function updateTask(id: string, formData: FormData) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const validated = UpdateTaskSchema.parse(Object.fromEntries(formData) as Record<string, unknown>)
  await taskService.update(userId, id, validated)
  revalidatePath('/tasks')
  redirect('/tasks')
}

export async function deleteTask(id: string) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  await taskService.delete(userId, id)
  revalidatePath('/tasks')
  redirect('/tasks')
}
