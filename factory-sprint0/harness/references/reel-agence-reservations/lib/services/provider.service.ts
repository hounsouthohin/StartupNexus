// AUTO-GÉNÉRÉ PAR dev_service_generator.py — NE PAS MODIFIER
import { notFound } from 'next/navigation'
import prisma from '@/lib/prisma'
import type { Provider } from '@prisma/client'
import type { CreateProviderInput, UpdateProviderInput, SerializedProvider } from '@/lib/types'

const _serialize = (item: Provider): SerializedProvider => {
  const rest = item
  return ({
    ...rest,
  createdAt: rest.createdAt.toISOString(),
  updatedAt: rest.updatedAt.toISOString(),
  }) as SerializedProvider
}

export const providerService = {
  getAll: async (userId: string, page: number = 1, pageSize: number = 20): Promise<SerializedProvider[]> => {
    const items = await prisma.provider.findMany({ where: {  }, select: { id: true, name: true, email: true, createdAt: true, updatedAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedProvider[]
  },

  getById: async (userId: string, id: string): Promise<SerializedProvider> => {
    const item = await prisma.provider.findFirst({ where: { id } })
    if (!item) notFound()
    return _serialize(item)
  },

  create: async (userId: string, data: CreateProviderInput): Promise<SerializedProvider> => {
    const { managerIds, ...rest } = data
    const _valid_managerIds = managerIds && managerIds.length
      ? (await prisma.manager.findMany({ where: { id: { in: managerIds } }, select: { id: true } })).map(_r => _r.id)
      : []
    const result = await prisma.provider.create({
      data: { ...rest, ...(_valid_managerIds.length ? { managers: { connect: _valid_managerIds.map(_id => ({ id: _id })) } } : {}) }
    })
    return _serialize(result)
  },

  update: async (userId: string, id: string, data: UpdateProviderInput): Promise<SerializedProvider> => {
    const { managerIds, ...rest } = data
    const _valid_managerIds = managerIds && managerIds.length
      ? (await prisma.manager.findMany({ where: { id: { in: managerIds } }, select: { id: true } })).map(_r => _r.id)
      : []
    const result = await prisma.provider.update({
      where: { id },
      data: { ...rest, ...(managerIds !== undefined ? { managers: { set: _valid_managerIds.map(_id => ({ id: _id })) } } : {}) }
    })
    return _serialize(result)
  },

  delete: async (userId: string, id: string): Promise<void> => {
    await prisma.provider.delete({ where: { id } })
  },

  getAllWithRelations: async (userId: string, page: number = 1, pageSize: number = 20): Promise<SerializedProvider[]> => {
    const items = await prisma.provider.findMany({ where: { userId }, select: { id: true, name: true, email: true, createdAt: true, updatedAt: true, managers: { select: { id: true, name: true, email: true } }, clients: { select: { id: true, name: true, email: true } }, reservations: { select: { id: true, date: true, status: true } } }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString(), reservations: (item.reservations ?? []).map(c => ({ ...c, date: c.date.toISOString() })) })) as SerializedProvider[]
  },

  getByIdWithRelations: async (userId: string, id: string): Promise<SerializedProvider> => {
    const item = await prisma.provider.findFirst({ where: { id, userId }, select: { id: true, name: true, email: true, createdAt: true, updatedAt: true, managers: { select: { id: true, name: true, email: true } }, clients: { select: { id: true, name: true, email: true } }, reservations: { select: { id: true, date: true, status: true } } } })
    if (!item) notFound()
    return (item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString(), reservations: (item.reservations ?? []).map(c => ({ ...c, date: c.date.toISOString() })) }))(item) as SerializedProvider
  },
}
