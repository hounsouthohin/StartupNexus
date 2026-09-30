// AUTO-GÉNÉRÉ PAR dev_actions_generator.py — NE PAS MODIFIER
'use server'

import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import { revalidatePath } from 'next/cache'
import { ZodError } from 'zod'
import { bookService } from '@/lib/services/book.service'
import { CreateBookSchema, UpdateBookSchema } from '@/lib/schemas'

export async function createBook(formData: FormData) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    const validated = CreateBookSchema.parse(Object.fromEntries(formData) as Record<string, unknown>)
    await bookService.create(userId, validated)
  } catch (e) {
    if (e instanceof ZodError) throw new Error(e.errors.map(err => err.message).join(', '))
    throw new Error('Une erreur est survenue. Veuillez réessayer.')
  }
  revalidatePath('/books')
  redirect('/books')
}

export async function updateBook(id: string, formData: FormData) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    const validated = UpdateBookSchema.parse(Object.fromEntries(formData) as Record<string, unknown>)
    await bookService.update(userId, id, validated)
  } catch (e) {
    if (e instanceof ZodError) throw new Error(e.errors.map(err => err.message).join(', '))
    throw new Error('Une erreur est survenue. Veuillez réessayer.')
  }
  revalidatePath('/books')
  redirect('/books')
}

export async function deleteBook(id: string) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    await bookService.delete(userId, id)
  } catch {
    return { error: 'Impossible de supprimer cet élément.' }
  }
  revalidatePath('/books')
  redirect('/books')
}
