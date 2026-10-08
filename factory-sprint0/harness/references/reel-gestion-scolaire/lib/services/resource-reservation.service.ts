// AUTO-GÉNÉRÉ PAR dev_service_generator.py — NE PAS MODIFIER
import { notFound } from 'next/navigation'
import prisma from '@/lib/prisma'
import type { ResourceReservation } from '@prisma/client'
import type { CreateResourceReservationInput, UpdateResourceReservationInput, SerializedResourceReservation } from '@/lib/types'

const _serialize = (item: ResourceReservation): SerializedResourceReservation => {
  const { userId: _owner, ...rest } = item
  return ({
    ...rest,
  date: rest.date.toISOString(),
  createdAt: rest.createdAt.toISOString(),
  updatedAt: rest.updatedAt.toISOString(),
  }) as SerializedResourceReservation
}

export const resourceReservationService = {
  getAll: async (userId: string, page: number = 1, pageSize: number = 20): Promise<SerializedResourceReservation[]> => {
    const items = await prisma.resourceReservation.findMany({ where: { userId }, select: { id: true, resourceId: true, date: true, createdAt: true, updatedAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, date: item.date.toISOString(), createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedResourceReservation[]
  },

  getAllAsAdmin: async (page: number = 1, pageSize: number = 20): Promise<SerializedResourceReservation[]> => {
    const items = await prisma.resourceReservation.findMany({ select: { id: true, resourceId: true, date: true, createdAt: true, updatedAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, date: item.date.toISOString(), createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedResourceReservation[]
  },

  getByIdAsAdmin: async (id: string): Promise<SerializedResourceReservation> => {
    const item = await prisma.resourceReservation.findFirst({ where: { id } })
    if (!item) notFound()
    return _serialize(item)
  },

  getById: async (userId: string, id: string): Promise<SerializedResourceReservation> => {
    const item = await prisma.resourceReservation.findFirst({ where: { id, userId } })
    if (!item) notFound()
    return _serialize(item)
  },

  create: async (userId: string, data: CreateResourceReservationInput): Promise<SerializedResourceReservation> => {
    if (data.resourceId) {
      const _owned_resourceId = await prisma.digitalResource.findFirst({ where: { id: data.resourceId, userId: userId }, select: { id: true } })
      if (!_owned_resourceId) throw new Error('Référence liée introuvable.')
    }
    const result = await prisma.resourceReservation.create({
      data: { ...data, userId }
    })
    return _serialize(result)
  },

  update: async (userId: string, id: string, data: UpdateResourceReservationInput): Promise<SerializedResourceReservation> => {
    if (data.resourceId) {
      const _owned_resourceId = await prisma.digitalResource.findFirst({ where: { id: data.resourceId, userId: userId }, select: { id: true } })
      if (!_owned_resourceId) throw new Error('Référence liée introuvable.')
    }
    const result = await prisma.resourceReservation.update({
      where: { id, userId },
      data: { ...data }
    })
    return _serialize(result)
  },

  delete: async (userId: string, id: string): Promise<void> => {
    await prisma.resourceReservation.delete({ where: { id, userId } })
  },

  getByDigitalResourceId: async (userId: string, resourceId: string, page: number = 1, pageSize: number = 20): Promise<SerializedResourceReservation[]> => {
    const items = await prisma.resourceReservation.findMany({ where: { resourceId, userId: userId }, select: { id: true, resourceId: true, date: true, createdAt: true, updatedAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, date: item.date.toISOString(), createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedResourceReservation[]
  },

  getAllWithRelations: async (userId: string, page: number = 1, pageSize: number = 20): Promise<SerializedResourceReservation[]> => {
    const items = await prisma.resourceReservation.findMany({ where: { userId }, select: { id: true, resourceId: true, date: true, createdAt: true, updatedAt: true, resource: { select: { id: true } } }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, date: item.date.toISOString(), createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedResourceReservation[]
  },

  getByIdWithRelations: async (userId: string, id: string): Promise<SerializedResourceReservation> => {
    const item = await prisma.resourceReservation.findFirst({ where: { id, userId }, select: { id: true, resourceId: true, date: true, createdAt: true, updatedAt: true, resource: { select: { id: true } } } })
    if (!item) notFound()
    return (item => ({ ...item, date: item.date.toISOString(), createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() }))(item) as SerializedResourceReservation
  },

  getByIdWithRelationsAsAdmin: async (id: string): Promise<SerializedResourceReservation> => {
    const item = await prisma.resourceReservation.findFirst({ where: { id }, select: { id: true, resourceId: true, date: true, createdAt: true, updatedAt: true, resource: { select: { id: true } } } })
    if (!item) notFound()
    return (item => ({ ...item, date: item.date.toISOString(), createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() }))(item) as SerializedResourceReservation
  },
}
