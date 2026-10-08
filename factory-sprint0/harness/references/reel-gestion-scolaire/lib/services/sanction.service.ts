// AUTO-GÉNÉRÉ PAR dev_service_generator.py — NE PAS MODIFIER
import { notFound } from 'next/navigation'
import prisma from '@/lib/prisma'
import type { Sanction } from '@prisma/client'
import type { CreateSanctionInput, UpdateSanctionInput, SerializedSanction } from '@/lib/types'

const _serialize = (item: Sanction): SerializedSanction => {
  const { userId: _owner, ...rest } = item
  return ({
    ...rest,
  createdAt: rest.createdAt.toISOString(),
  updatedAt: rest.updatedAt.toISOString(),
  }) as SerializedSanction
}

export const sanctionService = {
  getAll: async (userId: string, page: number = 1, pageSize: number = 20): Promise<SerializedSanction[]> => {
    const items = await prisma.sanction.findMany({ where: { userId }, select: { id: true, type: true, description: true, studentId: true, createdAt: true, updatedAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedSanction[]
  },

  getAllAsAdmin: async (page: number = 1, pageSize: number = 20): Promise<SerializedSanction[]> => {
    const items = await prisma.sanction.findMany({ select: { id: true, type: true, description: true, studentId: true, createdAt: true, updatedAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedSanction[]
  },

  getByIdAsAdmin: async (id: string): Promise<SerializedSanction> => {
    const item = await prisma.sanction.findFirst({ where: { id } })
    if (!item) notFound()
    return _serialize(item)
  },

  getById: async (userId: string, id: string): Promise<SerializedSanction> => {
    const item = await prisma.sanction.findFirst({ where: { id, userId } })
    if (!item) notFound()
    return _serialize(item)
  },

  create: async (userId: string, data: CreateSanctionInput): Promise<SerializedSanction> => {
    const result = await prisma.sanction.create({
      data: { ...data, userId }
    })
    return _serialize(result)
  },

  update: async (userId: string, id: string, data: UpdateSanctionInput): Promise<SerializedSanction> => {
    const result = await prisma.sanction.update({
      where: { id, userId },
      data: { ...data }
    })
    return _serialize(result)
  },

  delete: async (userId: string, id: string): Promise<void> => {
    await prisma.sanction.delete({ where: { id, userId } })
  },

  getAllWithRelations: async (userId: string, page: number = 1, pageSize: number = 20): Promise<SerializedSanction[]> => {
    const items = await prisma.sanction.findMany({ where: { userId }, select: { id: true, type: true, description: true, studentId: true, createdAt: true, updatedAt: true, student: { select: { id: true } } }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedSanction[]
  },

  getByIdWithRelations: async (userId: string, id: string): Promise<SerializedSanction> => {
    const item = await prisma.sanction.findFirst({ where: { id, userId }, select: { id: true, type: true, description: true, studentId: true, createdAt: true, updatedAt: true, student: { select: { id: true } } } })
    if (!item) notFound()
    return (item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() }))(item) as SerializedSanction
  },

  getByIdWithRelationsAsAdmin: async (id: string): Promise<SerializedSanction> => {
    const item = await prisma.sanction.findFirst({ where: { id }, select: { id: true, type: true, description: true, studentId: true, createdAt: true, updatedAt: true, student: { select: { id: true } } } })
    if (!item) notFound()
    return (item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() }))(item) as SerializedSanction
  },
}
