// AUTO-GÉNÉRÉ PAR dev_service_generator.py — NE PAS MODIFIER
import { notFound } from 'next/navigation'
import prisma from '@/lib/prisma'
import type { DSTPlanning } from '@prisma/client'
import type { CreateDSTPlanningInput, UpdateDSTPlanningInput, SerializedDSTPlanning } from '@/lib/types'

const _serialize = (item: DSTPlanning): SerializedDSTPlanning => {
  const { userId: _owner, ...rest } = item
  return ({
    ...rest,
  createdAt: rest.createdAt.toISOString(),
  updatedAt: rest.updatedAt.toISOString(),
  }) as SerializedDSTPlanning
}

export const dSTPlanningService = {
  getAll: async (userId: string, page: number = 1, pageSize: number = 20): Promise<SerializedDSTPlanning[]> => {
    const items = await prisma.dSTPlanning.findMany({ where: { userId }, select: { id: true, schedule: true, createdAt: true, updatedAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedDSTPlanning[]
  },

  getAllAsAdmin: async (page: number = 1, pageSize: number = 20): Promise<SerializedDSTPlanning[]> => {
    const items = await prisma.dSTPlanning.findMany({ select: { id: true, schedule: true, createdAt: true, updatedAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedDSTPlanning[]
  },

  getByIdAsAdmin: async (id: string): Promise<SerializedDSTPlanning> => {
    const item = await prisma.dSTPlanning.findFirst({ where: { id } })
    if (!item) notFound()
    return _serialize(item)
  },

  getById: async (userId: string, id: string): Promise<SerializedDSTPlanning> => {
    const item = await prisma.dSTPlanning.findFirst({ where: { id, userId } })
    if (!item) notFound()
    return _serialize(item)
  },

  create: async (userId: string, data: CreateDSTPlanningInput): Promise<SerializedDSTPlanning> => {
    const result = await prisma.dSTPlanning.create({
      data: { ...data, userId }
    })
    return _serialize(result)
  },

  update: async (userId: string, id: string, data: UpdateDSTPlanningInput): Promise<SerializedDSTPlanning> => {
    const result = await prisma.dSTPlanning.update({
      where: { id, userId },
      data: { ...data }
    })
    return _serialize(result)
  },

  delete: async (userId: string, id: string): Promise<void> => {
    await prisma.dSTPlanning.delete({ where: { id, userId } })
  },
}
