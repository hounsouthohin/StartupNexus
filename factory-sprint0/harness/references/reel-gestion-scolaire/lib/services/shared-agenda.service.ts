// AUTO-GÉNÉRÉ PAR dev_service_generator.py — NE PAS MODIFIER
import { notFound } from 'next/navigation'
import prisma from '@/lib/prisma'
import type { SharedAgenda } from '@prisma/client'
import type { CreateSharedAgendaInput, UpdateSharedAgendaInput, SerializedSharedAgenda } from '@/lib/types'

const _serialize = (item: SharedAgenda): SerializedSharedAgenda => {
  const { userId: _owner, ...rest } = item
  return ({
    ...rest,
  createdAt: rest.createdAt.toISOString(),
  updatedAt: rest.updatedAt.toISOString(),
  }) as SerializedSharedAgenda
}

export const sharedAgendaService = {
  getAll: async (userId: string, page: number = 1, pageSize: number = 20): Promise<SerializedSharedAgenda[]> => {
    const items = await prisma.sharedAgenda.findMany({ where: { userId }, select: { id: true, createdAt: true, updatedAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedSharedAgenda[]
  },

  getAllAsAdmin: async (page: number = 1, pageSize: number = 20): Promise<SerializedSharedAgenda[]> => {
    const items = await prisma.sharedAgenda.findMany({ select: { id: true, createdAt: true, updatedAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedSharedAgenda[]
  },

  getByIdAsAdmin: async (id: string): Promise<SerializedSharedAgenda> => {
    const item = await prisma.sharedAgenda.findFirst({ where: { id } })
    if (!item) notFound()
    return _serialize(item)
  },

  getById: async (userId: string, id: string): Promise<SerializedSharedAgenda> => {
    const item = await prisma.sharedAgenda.findFirst({ where: { id, userId } })
    if (!item) notFound()
    return _serialize(item)
  },

  create: async (userId: string, data: CreateSharedAgendaInput): Promise<SerializedSharedAgenda> => {
    const result = await prisma.sharedAgenda.create({
      data: { ...data, userId }
    })
    return _serialize(result)
  },

  update: async (userId: string, id: string, data: UpdateSharedAgendaInput): Promise<SerializedSharedAgenda> => {
    const result = await prisma.sharedAgenda.update({
      where: { id, userId },
      data: { ...data }
    })
    return _serialize(result)
  },

  delete: async (userId: string, id: string): Promise<void> => {
    await prisma.sharedAgenda.delete({ where: { id, userId } })
  },
}
