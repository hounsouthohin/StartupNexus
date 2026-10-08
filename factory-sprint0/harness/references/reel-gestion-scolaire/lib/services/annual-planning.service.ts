// AUTO-GÉNÉRÉ PAR dev_service_generator.py — NE PAS MODIFIER
import { notFound } from 'next/navigation'
import prisma from '@/lib/prisma'
import type { AnnualPlanning } from '@prisma/client'
import type { CreateAnnualPlanningInput, UpdateAnnualPlanningInput, SerializedAnnualPlanning } from '@/lib/types'

const _serialize = (item: AnnualPlanning): SerializedAnnualPlanning => {
  const { userId: _owner, ...rest } = item
  return ({
    ...rest,
  createdAt: rest.createdAt.toISOString(),
  updatedAt: rest.updatedAt.toISOString(),
  }) as SerializedAnnualPlanning
}

export const annualPlanningService = {
  getAll: async (userId: string, page: number = 1, pageSize: number = 20): Promise<SerializedAnnualPlanning[]> => {
    const items = await prisma.annualPlanning.findMany({ where: { userId }, select: { id: true, year: true, createdAt: true, updatedAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedAnnualPlanning[]
  },

  getAllAsAdmin: async (page: number = 1, pageSize: number = 20): Promise<SerializedAnnualPlanning[]> => {
    const items = await prisma.annualPlanning.findMany({ select: { id: true, year: true, createdAt: true, updatedAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedAnnualPlanning[]
  },

  getByIdAsAdmin: async (id: string): Promise<SerializedAnnualPlanning> => {
    const item = await prisma.annualPlanning.findFirst({ where: { id } })
    if (!item) notFound()
    return _serialize(item)
  },

  getById: async (userId: string, id: string): Promise<SerializedAnnualPlanning> => {
    const item = await prisma.annualPlanning.findFirst({ where: { id, userId } })
    if (!item) notFound()
    return _serialize(item)
  },

  create: async (userId: string, data: CreateAnnualPlanningInput): Promise<SerializedAnnualPlanning> => {
    const result = await prisma.annualPlanning.create({
      data: { ...data, userId }
    })
    return _serialize(result)
  },

  update: async (userId: string, id: string, data: UpdateAnnualPlanningInput): Promise<SerializedAnnualPlanning> => {
    const result = await prisma.annualPlanning.update({
      where: { id, userId },
      data: { ...data }
    })
    return _serialize(result)
  },

  delete: async (userId: string, id: string): Promise<void> => {
    await prisma.annualPlanning.delete({ where: { id, userId } })
  },
}
