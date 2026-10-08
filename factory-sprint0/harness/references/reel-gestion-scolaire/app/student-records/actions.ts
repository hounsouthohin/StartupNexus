// AUTO-GÉNÉRÉ PAR dev_actions_generator.py — NE PAS MODIFIER
'use server'

import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import { revalidatePath } from 'next/cache'
import { ZodError } from 'zod'
import { studentRecordService } from '@/lib/services/student-record.service'
import { CreateStudentRecordSchema, UpdateStudentRecordSchema } from '@/lib/schemas'

export async function createStudentRecord(formData: FormData) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    const _raw = Object.fromEntries(formData) as Record<string, unknown>
    _raw.courseIds = formData.getAll('courseIds').map(String).filter(v => v.length > 0)
    _raw.internshipIds = formData.getAll('internshipIds').map(String).filter(v => v.length > 0)
    _raw.foreignExchangeIds = formData.getAll('foreignExchangeIds').map(String).filter(v => v.length > 0)
    _raw.projectIds = formData.getAll('projectIds').map(String).filter(v => v.length > 0)
    _raw.continuousAssessmentIds = formData.getAll('continuousAssessmentIds').map(String).filter(v => v.length > 0)
    _raw.examIds = formData.getAll('examIds').map(String).filter(v => v.length > 0)
    _raw.defenseIds = formData.getAll('defenseIds').map(String).filter(v => v.length > 0)
    const validated = CreateStudentRecordSchema.parse(_raw)
    await studentRecordService.create(userId, validated)
  } catch (e) {
    if (e instanceof ZodError) throw new Error(e.errors.map(err => err.message).join(', '))
    throw new Error('Une erreur est survenue. Veuillez réessayer.')
  }
  revalidatePath('/student-records')
  redirect('/student-records')
}

export async function updateStudentRecord(id: string, formData: FormData) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    const _raw = Object.fromEntries(formData) as Record<string, unknown>
    _raw.courseIds = formData.getAll('courseIds').map(String).filter(v => v.length > 0)
    _raw.internshipIds = formData.getAll('internshipIds').map(String).filter(v => v.length > 0)
    _raw.foreignExchangeIds = formData.getAll('foreignExchangeIds').map(String).filter(v => v.length > 0)
    _raw.projectIds = formData.getAll('projectIds').map(String).filter(v => v.length > 0)
    _raw.continuousAssessmentIds = formData.getAll('continuousAssessmentIds').map(String).filter(v => v.length > 0)
    _raw.examIds = formData.getAll('examIds').map(String).filter(v => v.length > 0)
    _raw.defenseIds = formData.getAll('defenseIds').map(String).filter(v => v.length > 0)
    const validated = UpdateStudentRecordSchema.parse(_raw)
    await studentRecordService.update(userId, id, validated)
  } catch (e) {
    if (e instanceof ZodError) throw new Error(e.errors.map(err => err.message).join(', '))
    throw new Error('Une erreur est survenue. Veuillez réessayer.')
  }
  revalidatePath('/student-records')
  redirect('/student-records')
}

export async function deleteStudentRecord(id: string) {
  const { userId } = await auth()
  if (!userId) redirect('/sign-in')
  try {
    await studentRecordService.delete(userId, id)
  } catch {
    return { error: 'Impossible de supprimer cet élément.' }
  }
  revalidatePath('/student-records')
  redirect('/student-records')
}
