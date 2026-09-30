// AUTO-GÉNÉRÉ PAR dev_service_generator.py — NE PAS MODIFIER
import { notFound } from 'next/navigation'
import prisma from '@/lib/prisma'
import type { Space } from '@prisma/client'
import type { CreateSpaceInput, UpdateSpaceInput, SerializedSpace } from '@/lib/types'

const _serialize = (item: Space): SerializedSpace => {
  const rest = item
  return ({
    ...rest,
  createdAt: rest.createdAt.toISOString(),
  updatedAt: rest.updatedAt.toISOString(),
  }) as SerializedSpace
}

export const spaceService = {
  getAll: async (userId: string, page: number = 1, pageSize: number = 20): Promise<SerializedSpace[]> => {
    const items = await prisma.space.findMany({ where: {  }, select: { id: true, name: true, description: true, type: true, capacity: true, hourlyRate: true, address: true, createdAt: true, updatedAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedSpace[]
  },

  getById: async (userId: string, id: string): Promise<SerializedSpace> => {
    const item = await prisma.space.findFirst({ where: { id } })
    if (!item) notFound()
    return _serialize(item)
  },

  create: async (userId: string, data: CreateSpaceInput): Promise<SerializedSpace> => {
    const result = await prisma.space.create({
      data: { ...data }
    })
    return _serialize(result)
  },

  update: async (userId: string, id: string, data: UpdateSpaceInput): Promise<SerializedSpace> => {
    const result = await prisma.space.update({
      where: { id },
      data: { ...data }
    })
    return _serialize(result)
  },

  delete: async (userId: string, id: string): Promise<void> => {
    await prisma.space.delete({ where: { id } })
  },

  getPublicById: async (id: string): Promise<SerializedSpace> => {
    const item = await prisma.space.findUnique({ where: { id } })
    if (!item) notFound()
    return _serialize(item)
  },

  getPublicAll: async (page: number = 1, pageSize: number = 20): Promise<SerializedSpace[]> => {
    const items = await prisma.space.findMany({ select: { id: true, name: true, description: true, type: true, capacity: true, hourlyRate: true, address: true, createdAt: true, updatedAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedSpace[]
  },
}
