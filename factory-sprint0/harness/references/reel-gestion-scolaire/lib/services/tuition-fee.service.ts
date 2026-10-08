// AUTO-GÉNÉRÉ PAR dev_service_generator.py — NE PAS MODIFIER
import { notFound } from 'next/navigation'
import prisma from '@/lib/prisma'
import type { TuitionFee } from '@prisma/client'
import type { CreateTuitionFeeInput, UpdateTuitionFeeInput, SerializedTuitionFee } from '@/lib/types'

const _serialize = (item: TuitionFee): SerializedTuitionFee => {
  const { userId: _owner, ...rest } = item
  return ({
    ...rest,
  dueDate: rest.dueDate.toISOString(),
  createdAt: rest.createdAt.toISOString(),
  updatedAt: rest.updatedAt.toISOString(),
  }) as SerializedTuitionFee
}

export const tuitionFeeService = {
  getAll: async (userId: string, page: number = 1, pageSize: number = 20): Promise<SerializedTuitionFee[]> => {
    const items = await prisma.tuitionFee.findMany({ where: { userId }, select: { id: true, amount: true, dueDate: true, studentId: true, createdAt: true, updatedAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, dueDate: item.dueDate.toISOString(), createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedTuitionFee[]
  },

  getAllAsAdmin: async (page: number = 1, pageSize: number = 20): Promise<SerializedTuitionFee[]> => {
    const items = await prisma.tuitionFee.findMany({ select: { id: true, amount: true, dueDate: true, studentId: true, createdAt: true, updatedAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, dueDate: item.dueDate.toISOString(), createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedTuitionFee[]
  },

  getByIdAsAdmin: async (id: string): Promise<SerializedTuitionFee> => {
    const item = await prisma.tuitionFee.findFirst({ where: { id } })
    if (!item) notFound()
    return _serialize(item)
  },

  getById: async (userId: string, id: string): Promise<SerializedTuitionFee> => {
    const item = await prisma.tuitionFee.findFirst({ where: { id, userId } })
    if (!item) notFound()
    return _serialize(item)
  },

  create: async (userId: string, data: CreateTuitionFeeInput): Promise<SerializedTuitionFee> => {
    const result = await prisma.tuitionFee.create({
      data: { ...data, userId }
    })
    return _serialize(result)
  },

  update: async (userId: string, id: string, data: UpdateTuitionFeeInput): Promise<SerializedTuitionFee> => {
    const result = await prisma.tuitionFee.update({
      where: { id, userId },
      data: { ...data }
    })
    return _serialize(result)
  },

  delete: async (userId: string, id: string): Promise<void> => {
    await prisma.tuitionFee.delete({ where: { id, userId } })
  },

  getAllWithRelations: async (userId: string, page: number = 1, pageSize: number = 20): Promise<SerializedTuitionFee[]> => {
    const items = await prisma.tuitionFee.findMany({ where: { userId }, select: { id: true, amount: true, dueDate: true, studentId: true, createdAt: true, updatedAt: true, student: { select: { id: true } } }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, dueDate: item.dueDate.toISOString(), createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedTuitionFee[]
  },

  getByIdWithRelations: async (userId: string, id: string): Promise<SerializedTuitionFee> => {
    const item = await prisma.tuitionFee.findFirst({ where: { id, userId }, select: { id: true, amount: true, dueDate: true, studentId: true, createdAt: true, updatedAt: true, student: { select: { id: true } } } })
    if (!item) notFound()
    return (item => ({ ...item, dueDate: item.dueDate.toISOString(), createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() }))(item) as SerializedTuitionFee
  },

  getByIdWithRelationsAsAdmin: async (id: string): Promise<SerializedTuitionFee> => {
    const item = await prisma.tuitionFee.findFirst({ where: { id }, select: { id: true, amount: true, dueDate: true, studentId: true, createdAt: true, updatedAt: true, student: { select: { id: true } } } })
    if (!item) notFound()
    return (item => ({ ...item, dueDate: item.dueDate.toISOString(), createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() }))(item) as SerializedTuitionFee
  },
}
