// AUTO-GÉNÉRÉ PAR dev_service_generator.py — NE PAS MODIFIER
import { notFound } from 'next/navigation'
import prisma from '@/lib/prisma'
import type { DigitalResource } from '@prisma/client'
import type { CreateDigitalResourceInput, UpdateDigitalResourceInput, SerializedDigitalResource } from '@/lib/types'

const _serialize = (item: DigitalResource): SerializedDigitalResource => {
  const { userId: _owner, ...rest } = item
  return ({
    ...rest,
  createdAt: rest.createdAt.toISOString(),
  updatedAt: rest.updatedAt.toISOString(),
  }) as SerializedDigitalResource
}

export const digitalResourceService = {
  getAll: async (userId: string, page: number = 1, pageSize: number = 20): Promise<SerializedDigitalResource[]> => {
    const items = await prisma.digitalResource.findMany({ where: { userId }, select: { id: true, title: true, url: true, createdAt: true, updatedAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedDigitalResource[]
  },

  getAllAsAdmin: async (page: number = 1, pageSize: number = 20): Promise<SerializedDigitalResource[]> => {
    const items = await prisma.digitalResource.findMany({ select: { id: true, title: true, url: true, createdAt: true, updatedAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedDigitalResource[]
  },

  getByIdAsAdmin: async (id: string): Promise<SerializedDigitalResource> => {
    const item = await prisma.digitalResource.findFirst({ where: { id } })
    if (!item) notFound()
    return _serialize(item)
  },

  getById: async (userId: string, id: string): Promise<SerializedDigitalResource> => {
    const item = await prisma.digitalResource.findFirst({ where: { id, userId } })
    if (!item) notFound()
    return _serialize(item)
  },

  create: async (userId: string, data: CreateDigitalResourceInput): Promise<SerializedDigitalResource> => {
    const result = await prisma.digitalResource.create({
      data: { ...data, userId }
    })
    return _serialize(result)
  },

  update: async (userId: string, id: string, data: UpdateDigitalResourceInput): Promise<SerializedDigitalResource> => {
    const result = await prisma.digitalResource.update({
      where: { id, userId },
      data: { ...data }
    })
    return _serialize(result)
  },

  delete: async (userId: string, id: string): Promise<void> => {
    await prisma.digitalResource.delete({ where: { id, userId } })
  },
}
