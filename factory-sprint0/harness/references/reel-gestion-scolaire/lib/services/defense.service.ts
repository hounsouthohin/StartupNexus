// AUTO-GÉNÉRÉ PAR dev_service_generator.py — NE PAS MODIFIER
import { notFound } from 'next/navigation'
import prisma from '@/lib/prisma'
import type { Defense } from '@prisma/client'
import type { CreateDefenseInput, UpdateDefenseInput, SerializedDefense } from '@/lib/types'

const _serialize = (item: Defense): SerializedDefense => {
  const { userId: _owner, ...rest } = item
  return ({
    ...rest,
  date: rest.date.toISOString(),
  createdAt: rest.createdAt.toISOString(),
  updatedAt: rest.updatedAt.toISOString(),
  }) as SerializedDefense
}

export const defenseService = {
  getAll: async (userId: string, page: number = 1, pageSize: number = 20): Promise<SerializedDefense[]> => {
    const items = await prisma.defense.findMany({ where: { userId }, select: { id: true, topic: true, date: true, studentId: true, createdAt: true, updatedAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, date: item.date.toISOString(), createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedDefense[]
  },

  getAllAsAdmin: async (page: number = 1, pageSize: number = 20): Promise<SerializedDefense[]> => {
    const items = await prisma.defense.findMany({ select: { id: true, topic: true, date: true, studentId: true, createdAt: true, updatedAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, date: item.date.toISOString(), createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedDefense[]
  },

  getByIdAsAdmin: async (id: string): Promise<SerializedDefense> => {
    const item = await prisma.defense.findFirst({ where: { id } })
    if (!item) notFound()
    return _serialize(item)
  },

  getById: async (userId: string, id: string): Promise<SerializedDefense> => {
    const item = await prisma.defense.findFirst({ where: { id, userId } })
    if (!item) notFound()
    return _serialize(item)
  },

  create: async (userId: string, data: CreateDefenseInput): Promise<SerializedDefense> => {
    const result = await prisma.defense.create({
      data: { ...data, userId }
    })
    return _serialize(result)
  },

  update: async (userId: string, id: string, data: UpdateDefenseInput): Promise<SerializedDefense> => {
    const result = await prisma.defense.update({
      where: { id, userId },
      data: { ...data }
    })
    return _serialize(result)
  },

  delete: async (userId: string, id: string): Promise<void> => {
    await prisma.defense.delete({ where: { id, userId } })
  },

  getAllWithRelations: async (userId: string, page: number = 1, pageSize: number = 20): Promise<SerializedDefense[]> => {
    const items = await prisma.defense.findMany({ where: { userId }, select: { id: true, topic: true, date: true, studentId: true, createdAt: true, updatedAt: true, student: { select: { id: true } } }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, date: item.date.toISOString(), createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedDefense[]
  },

  getByIdWithRelations: async (userId: string, id: string): Promise<SerializedDefense> => {
    const item = await prisma.defense.findFirst({ where: { id, userId }, select: { id: true, topic: true, date: true, studentId: true, createdAt: true, updatedAt: true, student: { select: { id: true } } } })
    if (!item) notFound()
    return (item => ({ ...item, date: item.date.toISOString(), createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() }))(item) as SerializedDefense
  },

  getByIdWithRelationsAsAdmin: async (id: string): Promise<SerializedDefense> => {
    const item = await prisma.defense.findFirst({ where: { id }, select: { id: true, topic: true, date: true, studentId: true, createdAt: true, updatedAt: true, student: { select: { id: true } } } })
    if (!item) notFound()
    return (item => ({ ...item, date: item.date.toISOString(), createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() }))(item) as SerializedDefense
  },
}
