// AUTO-GÉNÉRÉ PAR dev_service_generator.py — NE PAS MODIFIER
import { notFound } from 'next/navigation'
import prisma from '@/lib/prisma'
import type { Grade } from '@prisma/client'
import type { CreateGradeInput, UpdateGradeInput, SerializedGrade } from '@/lib/types'

const _serialize = (item: Grade): SerializedGrade => {
  const { userId: _owner, ...rest } = item
  return ({
    ...rest,
  createdAt: rest.createdAt.toISOString(),
  updatedAt: rest.updatedAt.toISOString(),
  }) as SerializedGrade
}

export const gradeService = {
  getAll: async (userId: string, page: number = 1, pageSize: number = 20): Promise<SerializedGrade[]> => {
    const items = await prisma.grade.findMany({ where: { userId }, select: { id: true, value: true, courseId: true, studentId: true, createdAt: true, updatedAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedGrade[]
  },

  getAllAsAdmin: async (page: number = 1, pageSize: number = 20): Promise<SerializedGrade[]> => {
    const items = await prisma.grade.findMany({ select: { id: true, value: true, courseId: true, studentId: true, createdAt: true, updatedAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedGrade[]
  },

  getByIdAsAdmin: async (id: string): Promise<SerializedGrade> => {
    const item = await prisma.grade.findFirst({ where: { id } })
    if (!item) notFound()
    return _serialize(item)
  },

  getById: async (userId: string, id: string): Promise<SerializedGrade> => {
    const item = await prisma.grade.findFirst({ where: { id, userId } })
    if (!item) notFound()
    return _serialize(item)
  },

  create: async (userId: string, data: CreateGradeInput): Promise<SerializedGrade> => {
    if (data.courseId) {
      const _owned_courseId = await prisma.course.findFirst({ where: { id: data.courseId, userId: userId }, select: { id: true } })
      if (!_owned_courseId) throw new Error('Référence liée introuvable.')
    }
    const result = await prisma.grade.create({
      data: { ...data, userId }
    })
    return _serialize(result)
  },

  update: async (userId: string, id: string, data: UpdateGradeInput): Promise<SerializedGrade> => {
    if (data.courseId) {
      const _owned_courseId = await prisma.course.findFirst({ where: { id: data.courseId, userId: userId }, select: { id: true } })
      if (!_owned_courseId) throw new Error('Référence liée introuvable.')
    }
    const result = await prisma.grade.update({
      where: { id, userId },
      data: { ...data }
    })
    return _serialize(result)
  },

  delete: async (userId: string, id: string): Promise<void> => {
    await prisma.grade.delete({ where: { id, userId } })
  },

  getByCourseId: async (userId: string, courseId: string, page: number = 1, pageSize: number = 20): Promise<SerializedGrade[]> => {
    const items = await prisma.grade.findMany({ where: { courseId, userId: userId }, select: { id: true, value: true, courseId: true, studentId: true, createdAt: true, updatedAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedGrade[]
  },

  getAllWithRelations: async (userId: string, page: number = 1, pageSize: number = 20): Promise<SerializedGrade[]> => {
    const items = await prisma.grade.findMany({ where: { userId }, select: { id: true, value: true, courseId: true, studentId: true, createdAt: true, updatedAt: true, course: { select: { id: true, name: true, description: true, credits: true, coefficient: true } }, student: { select: { id: true } } }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedGrade[]
  },

  getByIdWithRelations: async (userId: string, id: string): Promise<SerializedGrade> => {
    const item = await prisma.grade.findFirst({ where: { id, userId }, select: { id: true, value: true, courseId: true, studentId: true, createdAt: true, updatedAt: true, course: { select: { id: true, name: true, description: true, credits: true, coefficient: true } }, student: { select: { id: true } } } })
    if (!item) notFound()
    return (item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() }))(item) as SerializedGrade
  },

  getByIdWithRelationsAsAdmin: async (id: string): Promise<SerializedGrade> => {
    const item = await prisma.grade.findFirst({ where: { id }, select: { id: true, value: true, courseId: true, studentId: true, createdAt: true, updatedAt: true, course: { select: { id: true, name: true, description: true, credits: true, coefficient: true } }, student: { select: { id: true } } } })
    if (!item) notFound()
    return (item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() }))(item) as SerializedGrade
  },
}
