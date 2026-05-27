// AUTO-GÉNÉRÉ PAR dev_actions_generator.py — NE PAS MODIFIER
'use server'

import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import { revalidatePath } from 'next/cache'
import { leaveRequestService } from '@/lib/services/leave-request.service'
import { CreateLeaveRequestSchema, UpdateLeaveRequestSchema } from '@/lib/schemas'

export async function createLeaveRequest(formData: FormData) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const validated = CreateLeaveRequestSchema.parse(Object.fromEntries(formData) as Record<string, unknown>)
  await leaveRequestService.create(userId, validated)
  revalidatePath('/leave-requests')
  redirect('/leave-requests')
}

export async function updateLeaveRequest(id: string, formData: FormData) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  const validated = UpdateLeaveRequestSchema.parse(Object.fromEntries(formData) as Record<string, unknown>)
  await leaveRequestService.update(userId, id, validated)
  revalidatePath('/leave-requests')
  redirect('/leave-requests')
}

export async function deleteLeaveRequest(id: string) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  await leaveRequestService.delete(userId, id)
  revalidatePath('/leave-requests')
  redirect('/leave-requests')
}
