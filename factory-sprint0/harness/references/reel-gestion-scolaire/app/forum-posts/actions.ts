// AUTO-GÉNÉRÉ PAR dev_actions_generator.py — NE PAS MODIFIER
'use server'

import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import { revalidatePath } from 'next/cache'
import { ZodError } from 'zod'
import { forumPostService } from '@/lib/services/forum-post.service'
import { CreateForumPostSchema, UpdateForumPostSchema } from '@/lib/schemas'

export async function createForumPost(formData: FormData) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    const validated = CreateForumPostSchema.parse(Object.fromEntries(formData) as Record<string, unknown>)
    await forumPostService.create(userId, validated)
  } catch (e) {
    if (e instanceof ZodError) throw new Error(e.errors.map(err => err.message).join(', '))
    throw new Error('Une erreur est survenue. Veuillez réessayer.')
  }
  revalidatePath('/forum-posts')
  redirect('/forum-posts')
}

export async function updateForumPost(id: string, formData: FormData) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    const validated = UpdateForumPostSchema.parse(Object.fromEntries(formData) as Record<string, unknown>)
    await forumPostService.update(userId, id, validated)
  } catch (e) {
    if (e instanceof ZodError) throw new Error(e.errors.map(err => err.message).join(', '))
    throw new Error('Une erreur est survenue. Veuillez réessayer.')
  }
  revalidatePath('/forum-posts')
  redirect('/forum-posts')
}

export async function deleteForumPost(id: string) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    await forumPostService.delete(userId, id)
  } catch {
    return { error: 'Impossible de supprimer cet élément.' }
  }
  revalidatePath('/forum-posts')
  redirect('/forum-posts')
}
