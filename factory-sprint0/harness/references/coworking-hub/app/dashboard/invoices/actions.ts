// AUTO-GÉNÉRÉ PAR dev_actions_generator.py — NE PAS MODIFIER
'use server'

import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import { revalidatePath } from 'next/cache'
import { ZodError } from 'zod'
import { invoiceService } from '@/lib/services/invoice.service'
import { CreateInvoiceSchema, UpdateInvoiceSchema } from '@/lib/schemas'
import { requireRole, hasRole } from '@/lib/auth-role'

export async function createInvoice(formData: FormData) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    const validated = CreateInvoiceSchema.parse(Object.fromEntries(formData) as Record<string, unknown>)
    await invoiceService.create(userId, validated)
  } catch (e) {
    if (e instanceof ZodError) throw new Error(e.errors.map(err => err.message).join(', '))
    throw new Error('Une erreur est survenue. Veuillez réessayer.')
  }
  revalidatePath('/dashboard/invoices')
  redirect('/dashboard/invoices')
}

export async function updateInvoice(id: string, formData: FormData) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    const validated = UpdateInvoiceSchema.parse(Object.fromEntries(formData) as Record<string, unknown>)
    await invoiceService.update(userId, id, validated)
  } catch (e) {
    if (e instanceof ZodError) throw new Error(e.errors.map(err => err.message).join(', '))
    throw new Error('Une erreur est survenue. Veuillez réessayer.')
  }
  revalidatePath('/dashboard/invoices')
  redirect('/dashboard/invoices')
}

export async function transitionInvoice(id: string, newStatus: string, formData: FormData) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  await requireRole('admin')
  try {
    const data = UpdateInvoiceSchema.parse(Object.fromEntries(formData) as Record<string, unknown>)
    await invoiceService.transitionTo(userId, id, newStatus, data)
  } catch (e) {
    if (e instanceof ZodError) throw new Error(e.errors.map(err => err.message).join(', '))
    throw new Error('Une erreur est survenue. Veuillez réessayer.')
  }
  revalidatePath('/dashboard/invoices')
  redirect('/dashboard/invoices')
}

export async function deleteInvoice(id: string) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    await invoiceService.delete(userId, id)
  } catch {
    return { error: 'Impossible de supprimer cet élément.' }
  }
  revalidatePath('/dashboard/invoices')
  redirect('/dashboard/invoices')
}
