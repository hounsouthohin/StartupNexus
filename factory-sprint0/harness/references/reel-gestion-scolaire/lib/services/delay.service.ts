// AUTO-GÉNÉRÉ PAR dev_service_generator.py — NE PAS MODIFIER
import { notFound } from 'next/navigation'
import prisma from '@/lib/prisma'
import type { Delay } from '@prisma/client'
import type { CreateDelayInput, UpdateDelayInput, SerializedDelay } from '@/lib/types'

const _serialize = (item: Delay): SerializedDelay => {
  const { userId: _owner, ...rest } = item
  return ({
    ...rest,
  date: rest.date.toISOString(),
  createdAt: rest.createdAt.toISOString(),
  updatedAt: rest.updatedAt.toISOString(),
  }) as SerializedDelay
}

export const delayService = {
  getAll: async (userId: string, page: number = 1, pageSize: number = 20): Promise<SerializedDelay[]> => {
    const items = await prisma.delay.findMany({ where: { userId }, select: { id: true, date: true, reason: true, studentId: true, createdAt: true, updatedAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, date: item.date.toISOString(), createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedDelay[]
  },

  getAllAsAdmin: async (page: number = 1, pageSize: number = 20): Promise<SerializedDelay[]> => {
    const items = await prisma.delay.findMany({ select: { id: true, date: true, reason: true, studentId: true, createdAt: true, updatedAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, date: item.date.toISOString(), createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedDelay[]
  },

  getByIdAsAdmin: async (id: string): Promise<SerializedDelay> => {
    const item = await prisma.delay.findFirst({ where: { id } })
    if (!item) notFound()
    return _serialize(item)
  },

  getById: async (userId: string, id: string): Promise<SerializedDelay> => {
    const item = await prisma.delay.findFirst({ where: { id, userId } })
    if (!item) notFound()
    return _serialize(item)
  },

  create: async (userId: string, data: CreateDelayInput): Promise<SerializedDelay> => {
    const result = await prisma.delay.create({
      data: { ...data, userId }
    })
    return _serialize(result)
  },

  update: async (userId: string, id: string, data: UpdateDelayInput): Promise<SerializedDelay> => {
    const result = await prisma.delay.update({
      where: { id, userId },
      data: { ...data }
    })
    return _serialize(result)
  },

  delete: async (userId: string, id: string): Promise<void> => {
    await prisma.delay.delete({ where: { id, userId } })
  },

  getAllWithRelations: async (userId: string, page: number = 1, pageSize: number = 20): Promise<SerializedDelay[]> => {
    const items = await prisma.delay.findMany({ where: { userId }, select: { id: true, date: true, reason: true, studentId: true, createdAt: true, updatedAt: true, student: { select: { id: true } } }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, date: item.date.toISOString(), createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedDelay[]
  },

  getByIdWithRelations: async (userId: string, id: string): Promise<SerializedDelay> => {
    const item = await prisma.delay.findFirst({ where: { id, userId }, select: { id: true, date: true, reason: true, studentId: true, createdAt: true, updatedAt: true, student: { select: { id: true } } } })
    if (!item) notFound()
    return (item => ({ ...item, date: item.date.toISOString(), createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() }))(item) as SerializedDelay
  },

  getByIdWithRelationsAsAdmin: async (id: string): Promise<SerializedDelay> => {
    const item = await prisma.delay.findFirst({ where: { id }, select: { id: true, date: true, reason: true, studentId: true, createdAt: true, updatedAt: true, student: { select: { id: true } } } })
    if (!item) notFound()
    return (item => ({ ...item, date: item.date.toISOString(), createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() }))(item) as SerializedDelay
  },
}
