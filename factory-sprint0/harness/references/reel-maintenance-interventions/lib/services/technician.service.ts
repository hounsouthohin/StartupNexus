// AUTO-GÉNÉRÉ PAR dev_service_generator.py — NE PAS MODIFIER
import { notFound } from 'next/navigation'
import prisma from '@/lib/prisma'
import type { Technician } from '@prisma/client'
import type { CreateTechnicianInput, UpdateTechnicianInput, SerializedTechnician } from '@/lib/types'

const _serialize = (item: Technician): SerializedTechnician => {
  const { userId: _owner, ...rest } = item
  return ({
    ...rest,
  createdAt: rest.createdAt.toISOString(),
  updatedAt: rest.updatedAt.toISOString(),
  }) as SerializedTechnician
}

export const technicianService = {
  getAll: async (userId: string, page: number = 1, pageSize: number = 20): Promise<SerializedTechnician[]> => {
    const items = await prisma.technician.findMany({ where: { userId }, select: { id: true, name: true, email: true, phone: true, region: true, createdAt: true, updatedAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedTechnician[]
  },

  getById: async (userId: string, id: string): Promise<SerializedTechnician> => {
    const item = await prisma.technician.findFirst({ where: { id, userId } })
    if (!item) notFound()
    return _serialize(item)
  },

  create: async (userId: string, data: CreateTechnicianInput): Promise<SerializedTechnician> => {
    const result = await prisma.technician.create({
      data: { ...data, userId }
    })
    return _serialize(result)
  },

  update: async (userId: string, id: string, data: UpdateTechnicianInput): Promise<SerializedTechnician> => {
    const result = await prisma.technician.update({
      where: { id, userId },
      data: { ...data }
    })
    return _serialize(result)
  },

  delete: async (userId: string, id: string): Promise<void> => {
    await prisma.technician.delete({ where: { id, userId } })
  },

  getAllWithRelations: async (userId: string, page: number = 1, pageSize: number = 20): Promise<SerializedTechnician[]> => {
    const items = await prisma.technician.findMany({ where: { userId }, select: { id: true, name: true, email: true, phone: true, region: true, createdAt: true, updatedAt: true, interventions: { select: { id: true, date: true, status: true } } }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString(), interventions: (item.interventions ?? []).map(c => ({ ...c, date: c.date.toISOString() })) })) as SerializedTechnician[]
  },

  getByIdWithRelations: async (userId: string, id: string): Promise<SerializedTechnician> => {
    const item = await prisma.technician.findFirst({ where: { id, userId }, select: { id: true, name: true, email: true, phone: true, region: true, createdAt: true, updatedAt: true, interventions: { select: { id: true, date: true, status: true } } } })
    if (!item) notFound()
    return (item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString(), interventions: (item.interventions ?? []).map(c => ({ ...c, date: c.date.toISOString() })) }))(item) as SerializedTechnician
  },
}
