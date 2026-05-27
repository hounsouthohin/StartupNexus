// AUTO-GÉNÉRÉ PAR dev_actions_generator.py — NE PAS MODIFIER
'use server'

import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import { revalidatePath } from 'next/cache'
import { projectService } from '@/lib/services/project.service'
import { CreateProjectSchema, UpdateProjectSchema } from '@/lib/schemas'

export async function createProject(formData: FormData) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const validated = CreateProjectSchema.parse(Object.fromEntries(formData) as Record<string, unknown>)
  await projectService.create(userId, validated)
  revalidatePath('/projects')
  redirect('/projects')
}

export async function updateProject(id: string, formData: FormData) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const validated = UpdateProjectSchema.parse(Object.fromEntries(formData) as Record<string, unknown>)
  await projectService.update(userId, id, validated)
  revalidatePath('/projects')
  redirect('/projects')
}

export async function deleteProject(id: string) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  await projectService.delete(userId, id)
  revalidatePath('/projects')
  redirect('/projects')
}
