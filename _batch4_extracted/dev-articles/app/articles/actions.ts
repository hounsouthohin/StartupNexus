// AUTO-GÉNÉRÉ PAR dev_actions_generator.py — NE PAS MODIFIER
'use server'

import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import { revalidatePath } from 'next/cache'
import { articleService } from '@/lib/services/article.service'
import { CreateArticleSchema, UpdateArticleSchema } from '@/lib/schemas'

export async function createArticle(formData: FormData) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const validated = CreateArticleSchema.parse(Object.fromEntries(formData) as Record<string, unknown>)
  await articleService.create(userId, validated)
  revalidatePath('/articles')
  redirect('/articles')
}

export async function updateArticle(id: string, formData: FormData) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const validated = UpdateArticleSchema.parse(Object.fromEntries(formData) as Record<string, unknown>)
  await articleService.update(userId, id, validated)
  revalidatePath('/articles')
  redirect('/articles')
}

export async function deleteArticle(id: string) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  await articleService.delete(userId, id)
  revalidatePath('/articles')
  redirect('/articles')
}
