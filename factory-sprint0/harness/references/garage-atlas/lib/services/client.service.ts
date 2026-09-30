// AUTO-GÉNÉRÉ PAR dev_service_generator.py — NE PAS MODIFIER
import { notFound } from 'next/navigation'
import prisma from '@/lib/prisma'
import type { Client } from '@prisma/client'
import type { CreateClientInput, UpdateClientInput, SerializedClient } from '@/lib/types'

const _serialize = (item: Client): SerializedClient => {
  const { userId: _owner, ...rest } = item
  return ({
    ...rest,
  createdAt: rest.createdAt.toISOString(),
  updatedAt: rest.updatedAt.toISOString(),
  }) as SerializedClient
}

export const clientService = {
  getAll: async (userId: string, page: number = 1, pageSize: number = 20): Promise<SerializedClient[]> => {
    const items = await prisma.client.findMany({ where: { userId }, select: { id: true, name: true, phone: true, createdAt: true, updatedAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedClient[]
  },

  getById: async (userId: string, id: string): Promise<SerializedClient> => {
    const item = await prisma.client.findFirst({ where: { id, userId } })
    if (!item) notFound()
    return _serialize(item)
  },

  create: async (userId: string, data: CreateClientInput): Promise<SerializedClient> => {
    const result = await prisma.client.create({
      data: { ...data, userId }
    })
    return _serialize(result)
  },

  update: async (userId: string, id: string, data: UpdateClientInput): Promise<SerializedClient> => {
    const result = await prisma.client.update({
      where: { id, userId },
      data: { ...data }
    })
    return _serialize(result)
  },

  delete: async (userId: string, id: string): Promise<void> => {
    await prisma.client.delete({ where: { id, userId } })
  },

  getAllWithRelations: async (userId: string, page: number = 1, pageSize: number = 20): Promise<SerializedClient[]> => {
    const items = await prisma.client.findMany({ where: { userId }, select: { id: true, name: true, phone: true, createdAt: true, updatedAt: true, vehicles: { select: { id: true, brand: true, model: true, licensePlate: true } } }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedClient[]
  },

  getByIdWithRelations: async (userId: string, id: string): Promise<SerializedClient> => {
    const item = await prisma.client.findFirst({ where: { id, userId }, select: { id: true, name: true, phone: true, createdAt: true, updatedAt: true, vehicles: { select: { id: true, brand: true, model: true, licensePlate: true } } } })
    if (!item) notFound()
    return (item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() }))(item) as SerializedClient
  },
}
