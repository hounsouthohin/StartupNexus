// AUTO-GÉNÉRÉ PAR dev_service_generator.py — NE PAS MODIFIER
import { notFound } from 'next/navigation'
import prisma from '@/lib/prisma'
import type { Exemption } from '@prisma/client'
import type { CreateExemptionInput, UpdateExemptionInput, SerializedExemption } from '@/lib/types'

const _serialize = (item: Exemption): SerializedExemption => {
  const { userId: _owner, ...rest } = item
  return ({
    ...rest,
  createdAt: rest.createdAt.toISOString(),
  updatedAt: rest.updatedAt.toISOString(),
  }) as SerializedExemption
}

export const exemptionService = {
  getAll: async (userId: string, page: number = 1, pageSize: number = 20): Promise<SerializedExemption[]> => {
    const items = await prisma.exemption.findMany({ where: { userId }, select: { id: true, reason: true, studentId: true, createdAt: true, updatedAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedExemption[]
  },

  getAllAsAdmin: async (page: number = 1, pageSize: number = 20): Promise<SerializedExemption[]> => {
    const items = await prisma.exemption.findMany({ select: { id: true, reason: true, studentId: true, createdAt: true, updatedAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedExemption[]
  },

  getByIdAsAdmin: async (id: string): Promise<SerializedExemption> => {
    const item = await prisma.exemption.findFirst({ where: { id } })
    if (!item) notFound()
    return _serialize(item)
  },

  getById: async (userId: string, id: string): Promise<SerializedExemption> => {
    const item = await prisma.exemption.findFirst({ where: { id, userId } })
    if (!item) notFound()
    return _serialize(item)
  },

  create: async (userId: string, data: CreateExemptionInput): Promise<SerializedExemption> => {
    const result = await prisma.exemption.create({
      data: { ...data, userId }
    })
    return _serialize(result)
  },

  update: async (userId: string, id: string, data: UpdateExemptionInput): Promise<SerializedExemption> => {
    const result = await prisma.exemption.update({
      where: { id, userId },
      data: { ...data }
    })
    return _serialize(result)
  },

  delete: async (userId: string, id: string): Promise<void> => {
    await prisma.exemption.delete({ where: { id, userId } })
  },

  getAllWithRelations: async (userId: string, page: number = 1, pageSize: number = 20): Promise<SerializedExemption[]> => {
    const items = await prisma.exemption.findMany({ where: { userId }, select: { id: true, reason: true, studentId: true, createdAt: true, updatedAt: true, student: { select: { id: true } } }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedExemption[]
  },

  getByIdWithRelations: async (userId: string, id: string): Promise<SerializedExemption> => {
    const item = await prisma.exemption.findFirst({ where: { id, userId }, select: { id: true, reason: true, studentId: true, createdAt: true, updatedAt: true, student: { select: { id: true } } } })
    if (!item) notFound()
    return (item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() }))(item) as SerializedExemption
  },

  getByIdWithRelationsAsAdmin: async (id: string): Promise<SerializedExemption> => {
    const item = await prisma.exemption.findFirst({ where: { id }, select: { id: true, reason: true, studentId: true, createdAt: true, updatedAt: true, student: { select: { id: true } } } })
    if (!item) notFound()
    return (item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() }))(item) as SerializedExemption
  },
}
