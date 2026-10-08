// AUTO-GÉNÉRÉ PAR dev_service_generator.py — NE PAS MODIFIER
import { notFound } from 'next/navigation'
import prisma from '@/lib/prisma'
import type { ForeignExchange } from '@prisma/client'
import type { CreateForeignExchangeInput, UpdateForeignExchangeInput, SerializedForeignExchange } from '@/lib/types'

const _serialize = (item: ForeignExchange): SerializedForeignExchange => {
  const { userId: _owner, ...rest } = item
  return ({
    ...rest,
  createdAt: rest.createdAt.toISOString(),
  updatedAt: rest.updatedAt.toISOString(),
  }) as SerializedForeignExchange
}

export const foreignExchangeService = {
  getAll: async (userId: string, page: number = 1, pageSize: number = 20): Promise<SerializedForeignExchange[]> => {
    const items = await prisma.foreignExchange.findMany({ where: { userId }, select: { id: true, country: true, duration: true, studentId: true, createdAt: true, updatedAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedForeignExchange[]
  },

  getAllAsAdmin: async (page: number = 1, pageSize: number = 20): Promise<SerializedForeignExchange[]> => {
    const items = await prisma.foreignExchange.findMany({ select: { id: true, country: true, duration: true, studentId: true, createdAt: true, updatedAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedForeignExchange[]
  },

  getByIdAsAdmin: async (id: string): Promise<SerializedForeignExchange> => {
    const item = await prisma.foreignExchange.findFirst({ where: { id } })
    if (!item) notFound()
    return _serialize(item)
  },

  getById: async (userId: string, id: string): Promise<SerializedForeignExchange> => {
    const item = await prisma.foreignExchange.findFirst({ where: { id, userId } })
    if (!item) notFound()
    return _serialize(item)
  },

  create: async (userId: string, data: CreateForeignExchangeInput): Promise<SerializedForeignExchange> => {
    const result = await prisma.foreignExchange.create({
      data: { ...data, userId }
    })
    return _serialize(result)
  },

  update: async (userId: string, id: string, data: UpdateForeignExchangeInput): Promise<SerializedForeignExchange> => {
    const result = await prisma.foreignExchange.update({
      where: { id, userId },
      data: { ...data }
    })
    return _serialize(result)
  },

  delete: async (userId: string, id: string): Promise<void> => {
    await prisma.foreignExchange.delete({ where: { id, userId } })
  },

  getAllWithRelations: async (userId: string, page: number = 1, pageSize: number = 20): Promise<SerializedForeignExchange[]> => {
    const items = await prisma.foreignExchange.findMany({ where: { userId }, select: { id: true, country: true, duration: true, studentId: true, createdAt: true, updatedAt: true, student: { select: { id: true } } }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedForeignExchange[]
  },

  getByIdWithRelations: async (userId: string, id: string): Promise<SerializedForeignExchange> => {
    const item = await prisma.foreignExchange.findFirst({ where: { id, userId }, select: { id: true, country: true, duration: true, studentId: true, createdAt: true, updatedAt: true, student: { select: { id: true } } } })
    if (!item) notFound()
    return (item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() }))(item) as SerializedForeignExchange
  },

  getByIdWithRelationsAsAdmin: async (id: string): Promise<SerializedForeignExchange> => {
    const item = await prisma.foreignExchange.findFirst({ where: { id }, select: { id: true, country: true, duration: true, studentId: true, createdAt: true, updatedAt: true, student: { select: { id: true } } } })
    if (!item) notFound()
    return (item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() }))(item) as SerializedForeignExchange
  },
}
