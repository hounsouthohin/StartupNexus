// AUTO-GÉNÉRÉ PAR dev_service_generator.py — NE PAS MODIFIER
import { notFound } from 'next/navigation'
import prisma from '@/lib/prisma'
import type { Exam } from '@prisma/client'
import type { CreateExamInput, UpdateExamInput, SerializedExam } from '@/lib/types'

const _serialize = (item: Exam): SerializedExam => {
  const { userId: _owner, ...rest } = item
  return ({
    ...rest,
  date: rest.date.toISOString(),
  createdAt: rest.createdAt.toISOString(),
  updatedAt: rest.updatedAt.toISOString(),
  }) as SerializedExam
}

export const examService = {
  getAll: async (userId: string, page: number = 1, pageSize: number = 20): Promise<SerializedExam[]> => {
    const items = await prisma.exam.findMany({ where: { userId }, select: { id: true, subject: true, date: true, studentId: true, createdAt: true, updatedAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, date: item.date.toISOString(), createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedExam[]
  },

  getAllAsAdmin: async (page: number = 1, pageSize: number = 20): Promise<SerializedExam[]> => {
    const items = await prisma.exam.findMany({ select: { id: true, subject: true, date: true, studentId: true, createdAt: true, updatedAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, date: item.date.toISOString(), createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedExam[]
  },

  getByIdAsAdmin: async (id: string): Promise<SerializedExam> => {
    const item = await prisma.exam.findFirst({ where: { id } })
    if (!item) notFound()
    return _serialize(item)
  },

  getById: async (userId: string, id: string): Promise<SerializedExam> => {
    const item = await prisma.exam.findFirst({ where: { id, userId } })
    if (!item) notFound()
    return _serialize(item)
  },

  create: async (userId: string, data: CreateExamInput): Promise<SerializedExam> => {
    const result = await prisma.exam.create({
      data: { ...data, userId }
    })
    return _serialize(result)
  },

  update: async (userId: string, id: string, data: UpdateExamInput): Promise<SerializedExam> => {
    const result = await prisma.exam.update({
      where: { id, userId },
      data: { ...data }
    })
    return _serialize(result)
  },

  delete: async (userId: string, id: string): Promise<void> => {
    await prisma.exam.delete({ where: { id, userId } })
  },

  getAllWithRelations: async (userId: string, page: number = 1, pageSize: number = 20): Promise<SerializedExam[]> => {
    const items = await prisma.exam.findMany({ where: { userId }, select: { id: true, subject: true, date: true, studentId: true, createdAt: true, updatedAt: true, student: { select: { id: true } } }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, date: item.date.toISOString(), createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedExam[]
  },

  getByIdWithRelations: async (userId: string, id: string): Promise<SerializedExam> => {
    const item = await prisma.exam.findFirst({ where: { id, userId }, select: { id: true, subject: true, date: true, studentId: true, createdAt: true, updatedAt: true, student: { select: { id: true } } } })
    if (!item) notFound()
    return (item => ({ ...item, date: item.date.toISOString(), createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() }))(item) as SerializedExam
  },

  getByIdWithRelationsAsAdmin: async (id: string): Promise<SerializedExam> => {
    const item = await prisma.exam.findFirst({ where: { id }, select: { id: true, subject: true, date: true, studentId: true, createdAt: true, updatedAt: true, student: { select: { id: true } } } })
    if (!item) notFound()
    return (item => ({ ...item, date: item.date.toISOString(), createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() }))(item) as SerializedExam
  },
}
