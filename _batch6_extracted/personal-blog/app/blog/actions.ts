// AUTO-GÉNÉRÉ PAR dev_actions_generator.py — NE PAS MODIFIER
'use server'

import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import { revalidatePath } from 'next/cache'
import { postService } from '@/lib/services/post.service'
import { CreatePostSchema, UpdatePostSchema } from '@/lib/schemas'

export async function createPost(formData: FormData) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const validated = CreatePostSchema.parse(Object.fromEntries(formData) as Record<string, unknown>)
  await postService.create(userId, validated)
  revalidatePath('/blog')
  redirect('/blog')
}

export async function updatePost(id: string, formData: FormData) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const validated = UpdatePostSchema.parse(Object.fromEntries(formData) as Record<string, unknown>)
  await postService.update(userId, id, validated)
  revalidatePath('/blog')
  redirect('/blog')
}

export async function deletePost(id: string) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  await postService.delete(userId, id)
  revalidatePath('/blog')
  redirect('/blog')
}
