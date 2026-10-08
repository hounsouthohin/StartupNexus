// AUTO-GÉNÉRÉ PAR dev_service_generator.py — NE PAS MODIFIER
import { notFound } from 'next/navigation'
import prisma from '@/lib/prisma'
import type { Client } from '@prisma/client'
import type { CreateClientInput, UpdateClientInput, SerializedClient } from '@/lib/types'

const _serialize = (item: Client): SerializedClient => {
  const { providerId: _owner, ...rest } = item
  return ({
    ...rest,
  createdAt: rest.createdAt.toISOString(),
  updatedAt: rest.updatedAt.toISOString(),
  }) as SerializedClient
}

export const clientService = {
  getAll: async (providerId: string, page: number = 1, pageSize: number = 20): Promise<SerializedClient[]> => {
    const items = await prisma.client.findMany({ where: { providerId }, select: { id: true, name: true, email: true, createdAt: true, updatedAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedClient[]
  },

  getAllAsAdmin: async (page: number = 1, pageSize: number = 20): Promise<SerializedClient[]> => {
    const items = await prisma.client.findMany({ select: { id: true, name: true, email: true, createdAt: true, updatedAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedClient[]
  },

  getByIdAsAdmin: async (id: string): Promise<SerializedClient> => {
    const item = await prisma.client.findFirst({ where: { id } })
    if (!item) notFound()
    return _serialize(item)
  },

  getById: async (providerId: string, id: string): Promise<SerializedClient> => {
    const item = await prisma.client.findFirst({ where: { id, providerId } })
    if (!item) notFound()
    return _serialize(item)
  },

  create: async (providerId: string, data: CreateClientInput): Promise<SerializedClient> => {
    const result = await prisma.client.create({
      data: { ...data, providerId }
    })
    return _serialize(result)
  },

  update: async (providerId: string, id: string, data: UpdateClientInput): Promise<SerializedClient> => {
    const result = await prisma.client.update({
      where: { id, providerId },
      data: { ...data }
    })
    return _serialize(result)
  },

  delete: async (providerId: string, id: string): Promise<void> => {
    await prisma.client.delete({ where: { id, providerId } })
  },

  getAllWithRelations: async (providerId: string, page: number = 1, pageSize: number = 20): Promise<SerializedClient[]> => {
    const items = await prisma.client.findMany({ where: { providerId }, select: { id: true, name: true, email: true, createdAt: true, updatedAt: true, provider: { select: { id: true, name: true, email: true } } }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedClient[]
  },

  getByIdWithRelations: async (providerId: string, id: string): Promise<SerializedClient> => {
    const item = await prisma.client.findFirst({ where: { id, providerId }, select: { id: true, name: true, email: true, createdAt: true, updatedAt: true, provider: { select: { id: true, name: true, email: true } } } })
    if (!item) notFound()
    return (item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() }))(item) as SerializedClient
  },

  getByIdWithRelationsAsAdmin: async (id: string): Promise<SerializedClient> => {
    const item = await prisma.client.findFirst({ where: { id }, select: { id: true, name: true, email: true, createdAt: true, updatedAt: true, provider: { select: { id: true, name: true, email: true } } } })
    if (!item) notFound()
    return (item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() }))(item) as SerializedClient
  },
}
