// AUTO-GÉNÉRÉ PAR dev_service_generator.py — NE PAS MODIFIER
import { notFound } from 'next/navigation'
import prisma from '@/lib/prisma'
import type { ContinuousAssessment } from '@prisma/client'
import type { CreateContinuousAssessmentInput, UpdateContinuousAssessmentInput, SerializedContinuousAssessment } from '@/lib/types'

const _serialize = (item: ContinuousAssessment): SerializedContinuousAssessment => {
  const { userId: _owner, ...rest } = item
  return ({
    ...rest,
  createdAt: rest.createdAt.toISOString(),
  updatedAt: rest.updatedAt.toISOString(),
  }) as SerializedContinuousAssessment
}

export const continuousAssessmentService = {
  getAll: async (userId: string, page: number = 1, pageSize: number = 20): Promise<SerializedContinuousAssessment[]> => {
    const items = await prisma.continuousAssessment.findMany({ where: { userId }, select: { id: true, score: true, courseId: true, studentId: true, createdAt: true, updatedAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedContinuousAssessment[]
  },

  getAllAsAdmin: async (page: number = 1, pageSize: number = 20): Promise<SerializedContinuousAssessment[]> => {
    const items = await prisma.continuousAssessment.findMany({ select: { id: true, score: true, courseId: true, studentId: true, createdAt: true, updatedAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedContinuousAssessment[]
  },

  getByIdAsAdmin: async (id: string): Promise<SerializedContinuousAssessment> => {
    const item = await prisma.continuousAssessment.findFirst({ where: { id } })
    if (!item) notFound()
    return _serialize(item)
  },

  getById: async (userId: string, id: string): Promise<SerializedContinuousAssessment> => {
    const item = await prisma.continuousAssessment.findFirst({ where: { id, userId } })
    if (!item) notFound()
    return _serialize(item)
  },

  create: async (userId: string, data: CreateContinuousAssessmentInput): Promise<SerializedContinuousAssessment> => {
    if (data.courseId) {
      const _owned_courseId = await prisma.course.findFirst({ where: { id: data.courseId, userId: userId }, select: { id: true } })
      if (!_owned_courseId) throw new Error('Référence liée introuvable.')
    }
    const result = await prisma.continuousAssessment.create({
      data: { ...data, userId }
    })
    return _serialize(result)
  },

  update: async (userId: string, id: string, data: UpdateContinuousAssessmentInput): Promise<SerializedContinuousAssessment> => {
    if (data.courseId) {
      const _owned_courseId = await prisma.course.findFirst({ where: { id: data.courseId, userId: userId }, select: { id: true } })
      if (!_owned_courseId) throw new Error('Référence liée introuvable.')
    }
    const result = await prisma.continuousAssessment.update({
      where: { id, userId },
      data: { ...data }
    })
    return _serialize(result)
  },

  delete: async (userId: string, id: string): Promise<void> => {
    await prisma.continuousAssessment.delete({ where: { id, userId } })
  },

  getByCourseId: async (userId: string, courseId: string, page: number = 1, pageSize: number = 20): Promise<SerializedContinuousAssessment[]> => {
    const items = await prisma.continuousAssessment.findMany({ where: { courseId, userId: userId }, select: { id: true, score: true, courseId: true, studentId: true, createdAt: true, updatedAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedContinuousAssessment[]
  },

  getAllWithRelations: async (userId: string, page: number = 1, pageSize: number = 20): Promise<SerializedContinuousAssessment[]> => {
    const items = await prisma.continuousAssessment.findMany({ where: { userId }, select: { id: true, score: true, courseId: true, studentId: true, createdAt: true, updatedAt: true, course: { select: { id: true, name: true, description: true, credits: true, coefficient: true } }, student: { select: { id: true } } }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedContinuousAssessment[]
  },

  getByIdWithRelations: async (userId: string, id: string): Promise<SerializedContinuousAssessment> => {
    const item = await prisma.continuousAssessment.findFirst({ where: { id, userId }, select: { id: true, score: true, courseId: true, studentId: true, createdAt: true, updatedAt: true, course: { select: { id: true, name: true, description: true, credits: true, coefficient: true } }, student: { select: { id: true } } } })
    if (!item) notFound()
    return (item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() }))(item) as SerializedContinuousAssessment
  },

  getByIdWithRelationsAsAdmin: async (id: string): Promise<SerializedContinuousAssessment> => {
    const item = await prisma.continuousAssessment.findFirst({ where: { id }, select: { id: true, score: true, courseId: true, studentId: true, createdAt: true, updatedAt: true, course: { select: { id: true, name: true, description: true, credits: true, coefficient: true } }, student: { select: { id: true } } } })
    if (!item) notFound()
    return (item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() }))(item) as SerializedContinuousAssessment
  },
}
