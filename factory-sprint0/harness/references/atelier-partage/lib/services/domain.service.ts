// AUTO-GÉNÉRÉ PAR dev_service_generator.py — NE PAS MODIFIER
import { notFound } from 'next/navigation'
import prisma from '@/lib/prisma'
import type { Domain } from '@prisma/client'
import type { CreateDomainInput, UpdateDomainInput, SerializedDomain } from '@/lib/types'

const _serialize = (item: Domain): SerializedDomain => {
  const rest = item
  return ({
    ...rest,
  createdAt: rest.createdAt.toISOString(),
  updatedAt: rest.updatedAt.toISOString(),
  }) as SerializedDomain
}

export const domainService = {
  getAll: async (userId: string, page: number = 1, pageSize: number = 20): Promise<SerializedDomain[]> => {
    const items = await prisma.domain.findMany({ where: {  }, select: { id: true, name: true, createdAt: true, updatedAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedDomain[]
  },

  getById: async (userId: string, id: string): Promise<SerializedDomain> => {
    const item = await prisma.domain.findFirst({ where: { id } })
    if (!item) notFound()
    return _serialize(item)
  },

  create: async (userId: string, data: CreateDomainInput): Promise<SerializedDomain> => {
    const { workshopIds, ...rest } = data
    const _valid_workshopIds = workshopIds && workshopIds.length
      ? (await prisma.workshop.findMany({ where: { id: { in: workshopIds } }, select: { id: true } })).map(_r => _r.id)
      : []
    const result = await prisma.domain.create({
      data: { ...rest, ...(_valid_workshopIds.length ? { workshops: { connect: _valid_workshopIds.map(_id => ({ id: _id })) } } : {}) }
    })
    return _serialize(result)
  },

  update: async (userId: string, id: string, data: UpdateDomainInput): Promise<SerializedDomain> => {
    const { workshopIds, ...rest } = data
    const _valid_workshopIds = workshopIds && workshopIds.length
      ? (await prisma.workshop.findMany({ where: { id: { in: workshopIds } }, select: { id: true } })).map(_r => _r.id)
      : []
    const result = await prisma.domain.update({
      where: { id },
      data: { ...rest, ...(workshopIds !== undefined ? { workshops: { set: _valid_workshopIds.map(_id => ({ id: _id })) } } : {}) }
    })
    return _serialize(result)
  },

  delete: async (userId: string, id: string): Promise<void> => {
    await prisma.domain.delete({ where: { id } })
  },

  getAllWithRelations: async (userId: string, page: number = 1, pageSize: number = 20): Promise<SerializedDomain[]> => {
    const items = await prisma.domain.findMany({ where: { userId }, select: { id: true, name: true, createdAt: true, updatedAt: true, workshops: { select: { id: true, title: true, description: true, duration: true, price: true } } }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedDomain[]
  },

  getByIdWithRelations: async (userId: string, id: string): Promise<SerializedDomain> => {
    const item = await prisma.domain.findFirst({ where: { id, userId }, select: { id: true, name: true, createdAt: true, updatedAt: true, workshops: { select: { id: true, title: true, description: true, duration: true, price: true } } } })
    if (!item) notFound()
    return (item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() }))(item) as SerializedDomain
  },
}
