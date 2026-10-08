// AUTO-GÉNÉRÉ PAR dev_service_generator.py — NE PAS MODIFIER
import { notFound } from 'next/navigation'
import prisma from '@/lib/prisma'
import type { Circular } from '@prisma/client'
import type { CreateCircularInput, UpdateCircularInput, SerializedCircular } from '@/lib/types'

const _serialize = (item: Circular): SerializedCircular => {
  const { userId: _owner, ...rest } = item
  return ({
    ...rest,
  createdAt: rest.createdAt.toISOString(),
  updatedAt: rest.updatedAt.toISOString(),
  }) as SerializedCircular
}

export const circularService = {
  getAll: async (userId: string, page: number = 1, pageSize: number = 20): Promise<SerializedCircular[]> => {
    const items = await prisma.circular.findMany({ where: { userId }, select: { id: true, title: true, content: true, createdAt: true, updatedAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedCircular[]
  },

  getAllAsAdmin: async (page: number = 1, pageSize: number = 20): Promise<SerializedCircular[]> => {
    const items = await prisma.circular.findMany({ select: { id: true, title: true, content: true, createdAt: true, updatedAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedCircular[]
  },

  getByIdAsAdmin: async (id: string): Promise<SerializedCircular> => {
    const item = await prisma.circular.findFirst({ where: { id } })
    if (!item) notFound()
    return _serialize(item)
  },

  getById: async (userId: string, id: string): Promise<SerializedCircular> => {
    const item = await prisma.circular.findFirst({ where: { id, userId } })
    if (!item) notFound()
    return _serialize(item)
  },

  create: async (userId: string, data: CreateCircularInput): Promise<SerializedCircular> => {
    const result = await prisma.circular.create({
      data: { ...data, userId }
    })
    return _serialize(result)
  },

  update: async (userId: string, id: string, data: UpdateCircularInput): Promise<SerializedCircular> => {
    const result = await prisma.circular.update({
      where: { id, userId },
      data: { ...data }
    })
    return _serialize(result)
  },

  delete: async (userId: string, id: string): Promise<void> => {
    await prisma.circular.delete({ where: { id, userId } })
  },
}
