// AUTO-GÉNÉRÉ PAR dev_service_generator.py — NE PAS MODIFIER
import { notFound } from 'next/navigation'
import prisma from '@/lib/prisma'
import type { CompetencyRecord } from '@prisma/client'
import type { CreateCompetencyRecordInput, UpdateCompetencyRecordInput, SerializedCompetencyRecord } from '@/lib/types'

const _serialize = (item: CompetencyRecord): SerializedCompetencyRecord => {
  const { userId: _owner, ...rest } = item
  return ({
    ...rest,
  createdAt: rest.createdAt.toISOString(),
  updatedAt: rest.updatedAt.toISOString(),
  }) as SerializedCompetencyRecord
}

export const competencyRecordService = {
  getAll: async (userId: string, page: number = 1, pageSize: number = 20): Promise<SerializedCompetencyRecord[]> => {
    const items = await prisma.competencyRecord.findMany({ where: { userId }, select: { id: true, studentId: true, createdAt: true, updatedAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedCompetencyRecord[]
  },

  getAllAsAdmin: async (page: number = 1, pageSize: number = 20): Promise<SerializedCompetencyRecord[]> => {
    const items = await prisma.competencyRecord.findMany({ select: { id: true, studentId: true, createdAt: true, updatedAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedCompetencyRecord[]
  },

  getByIdAsAdmin: async (id: string): Promise<SerializedCompetencyRecord> => {
    const item = await prisma.competencyRecord.findFirst({ where: { id } })
    if (!item) notFound()
    return _serialize(item)
  },

  getById: async (userId: string, id: string): Promise<SerializedCompetencyRecord> => {
    const item = await prisma.competencyRecord.findFirst({ where: { id, userId } })
    if (!item) notFound()
    return _serialize(item)
  },

  create: async (userId: string, data: CreateCompetencyRecordInput): Promise<SerializedCompetencyRecord> => {
    const result = await prisma.competencyRecord.create({
      data: { ...data, userId }
    })
    return _serialize(result)
  },

  update: async (userId: string, id: string, data: UpdateCompetencyRecordInput): Promise<SerializedCompetencyRecord> => {
    const result = await prisma.competencyRecord.update({
      where: { id, userId },
      data: { ...data }
    })
    return _serialize(result)
  },

  delete: async (userId: string, id: string): Promise<void> => {
    await prisma.competencyRecord.delete({ where: { id, userId } })
  },

  getAllWithRelations: async (userId: string, page: number = 1, pageSize: number = 20): Promise<SerializedCompetencyRecord[]> => {
    const items = await prisma.competencyRecord.findMany({ where: { userId }, select: { id: true, studentId: true, createdAt: true, updatedAt: true, student: { select: { id: true } } }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedCompetencyRecord[]
  },

  getByIdWithRelations: async (userId: string, id: string): Promise<SerializedCompetencyRecord> => {
    const item = await prisma.competencyRecord.findFirst({ where: { id, userId }, select: { id: true, studentId: true, createdAt: true, updatedAt: true, student: { select: { id: true } } } })
    if (!item) notFound()
    return (item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() }))(item) as SerializedCompetencyRecord
  },

  getByIdWithRelationsAsAdmin: async (id: string): Promise<SerializedCompetencyRecord> => {
    const item = await prisma.competencyRecord.findFirst({ where: { id }, select: { id: true, studentId: true, createdAt: true, updatedAt: true, student: { select: { id: true } } } })
    if (!item) notFound()
    return (item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() }))(item) as SerializedCompetencyRecord
  },
}
