// AUTO-GÉNÉRÉ PAR dev_service_generator.py — NE PAS MODIFIER
import { notFound } from 'next/navigation'
import prisma from '@/lib/prisma'
import type { Manager } from '@prisma/client'
import type { CreateManagerInput, UpdateManagerInput, SerializedManager } from '@/lib/types'

const _serialize = (item: Manager): SerializedManager => {
  const rest = item
  return ({
    ...rest,
  createdAt: rest.createdAt.toISOString(),
  updatedAt: rest.updatedAt.toISOString(),
  }) as SerializedManager
}

export const managerService = {
  getAll: async (userId: string, page: number = 1, pageSize: number = 20): Promise<SerializedManager[]> => {
    const items = await prisma.manager.findMany({ where: {  }, select: { id: true, name: true, email: true, createdAt: true, updatedAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedManager[]
  },

  getById: async (userId: string, id: string): Promise<SerializedManager> => {
    const item = await prisma.manager.findFirst({ where: { id } })
    if (!item) notFound()
    return _serialize(item)
  },

  create: async (userId: string, data: CreateManagerInput): Promise<SerializedManager> => {
    const { providerIds, ...rest } = data
    const _valid_providerIds = providerIds && providerIds.length
      ? (await prisma.provider.findMany({ where: { id: { in: providerIds } }, select: { id: true } })).map(_r => _r.id)
      : []
    const result = await prisma.manager.create({
      data: { ...rest, ...(_valid_providerIds.length ? { providers: { connect: _valid_providerIds.map(_id => ({ id: _id })) } } : {}) }
    })
    return _serialize(result)
  },

  update: async (userId: string, id: string, data: UpdateManagerInput): Promise<SerializedManager> => {
    const { providerIds, ...rest } = data
    const _valid_providerIds = providerIds && providerIds.length
      ? (await prisma.provider.findMany({ where: { id: { in: providerIds } }, select: { id: true } })).map(_r => _r.id)
      : []
    const result = await prisma.manager.update({
      where: { id },
      data: { ...rest, ...(providerIds !== undefined ? { providers: { set: _valid_providerIds.map(_id => ({ id: _id })) } } : {}) }
    })
    return _serialize(result)
  },

  delete: async (userId: string, id: string): Promise<void> => {
    await prisma.manager.delete({ where: { id } })
  },

  getAllWithRelations: async (userId: string, page: number = 1, pageSize: number = 20): Promise<SerializedManager[]> => {
    const items = await prisma.manager.findMany({ where: { userId }, select: { id: true, name: true, email: true, createdAt: true, updatedAt: true, providers: { select: { id: true, name: true, email: true } }, reservations: { select: { id: true, date: true, status: true } } }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString(), reservations: (item.reservations ?? []).map(c => ({ ...c, date: c.date.toISOString() })) })) as SerializedManager[]
  },

  getByIdWithRelations: async (userId: string, id: string): Promise<SerializedManager> => {
    const item = await prisma.manager.findFirst({ where: { id, userId }, select: { id: true, name: true, email: true, createdAt: true, updatedAt: true, providers: { select: { id: true, name: true, email: true } }, reservations: { select: { id: true, date: true, status: true } } } })
    if (!item) notFound()
    return (item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString(), reservations: (item.reservations ?? []).map(c => ({ ...c, date: c.date.toISOString() })) }))(item) as SerializedManager
  },
}
