// AUTO-GÉNÉRÉ PAR dev_service_generator.py — NE PAS MODIFIER
import { notFound } from 'next/navigation'
import prisma from '@/lib/prisma'
import type { Workshop } from '@prisma/client'
import type { CreateWorkshopInput, UpdateWorkshopInput, SerializedWorkshop } from '@/lib/types'

const _serialize = (item: Workshop): SerializedWorkshop => {
  const rest = item
  return ({
    ...rest,
  createdAt: rest.createdAt.toISOString(),
  updatedAt: rest.updatedAt.toISOString(),
  }) as SerializedWorkshop
}

export const workshopService = {
  getAll: async (userId: string, page: number = 1, pageSize: number = 20): Promise<SerializedWorkshop[]> => {
    const items = await prisma.workshop.findMany({ where: {  }, select: { id: true, title: true, description: true, duration: true, price: true, createdAt: true, updatedAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedWorkshop[]
  },

  getById: async (userId: string, id: string): Promise<SerializedWorkshop> => {
    const item = await prisma.workshop.findFirst({ where: { id } })
    if (!item) notFound()
    return _serialize(item)
  },

  create: async (userId: string, data: CreateWorkshopInput): Promise<SerializedWorkshop> => {
    const { domainIds, ...rest } = data
    const _valid_domainIds = domainIds && domainIds.length
      ? (await prisma.domain.findMany({ where: { id: { in: domainIds } }, select: { id: true } })).map(_r => _r.id)
      : []
    const result = await prisma.workshop.create({
      data: { ...rest, ...(_valid_domainIds.length ? { domains: { connect: _valid_domainIds.map(_id => ({ id: _id })) } } : {}) }
    })
    return _serialize(result)
  },

  update: async (userId: string, id: string, data: UpdateWorkshopInput): Promise<SerializedWorkshop> => {
    const { domainIds, ...rest } = data
    const _valid_domainIds = domainIds && domainIds.length
      ? (await prisma.domain.findMany({ where: { id: { in: domainIds } }, select: { id: true } })).map(_r => _r.id)
      : []
    const result = await prisma.workshop.update({
      where: { id },
      data: { ...rest, ...(domainIds !== undefined ? { domains: { set: _valid_domainIds.map(_id => ({ id: _id })) } } : {}) }
    })
    return _serialize(result)
  },

  delete: async (userId: string, id: string): Promise<void> => {
    await prisma.workshop.delete({ where: { id } })
  },

  getPublicById: async (id: string): Promise<SerializedWorkshop> => {
    const item = await prisma.workshop.findUnique({ where: { id } })
    if (!item) notFound()
    return _serialize(item)
  },

  getPublicAll: async (page: number = 1, pageSize: number = 20): Promise<SerializedWorkshop[]> => {
    const items = await prisma.workshop.findMany({ select: { id: true, title: true, description: true, duration: true, price: true, createdAt: true, updatedAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedWorkshop[]
  },

  getAllWithRelations: async (userId: string, page: number = 1, pageSize: number = 20): Promise<SerializedWorkshop[]> => {
    const items = await prisma.workshop.findMany({ where: { userId }, select: { id: true, title: true, description: true, duration: true, price: true, createdAt: true, updatedAt: true, domains: { select: { id: true, name: true } }, slots: { select: { id: true, startTime: true, endTime: true } } }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString(), slots: (item.slots ?? []).map(c => ({ ...c, startTime: c.startTime.toISOString(), endTime: c.endTime.toISOString() })) })) as SerializedWorkshop[]
  },

  getByIdWithRelations: async (userId: string, id: string): Promise<SerializedWorkshop> => {
    const item = await prisma.workshop.findFirst({ where: { id, userId }, select: { id: true, title: true, description: true, duration: true, price: true, createdAt: true, updatedAt: true, domains: { select: { id: true, name: true } }, slots: { select: { id: true, startTime: true, endTime: true } } } })
    if (!item) notFound()
    return (item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString(), slots: (item.slots ?? []).map(c => ({ ...c, startTime: c.startTime.toISOString(), endTime: c.endTime.toISOString() })) }))(item) as SerializedWorkshop
  },

  getPublicByIdWithRelations: async (id: string): Promise<SerializedWorkshop> => {
    const item = await prisma.workshop.findUnique({ where: { id }, select: { id: true, title: true, description: true, duration: true, price: true, createdAt: true, updatedAt: true, domains: { select: { id: true, name: true } }, slots: { select: { id: true, startTime: true, endTime: true } } } })
    if (!item) notFound()
    return (item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString(), slots: (item.slots ?? []).map(c => ({ ...c, startTime: c.startTime.toISOString(), endTime: c.endTime.toISOString() })) }))(item) as SerializedWorkshop
  },
}
