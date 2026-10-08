// AUTO-GÉNÉRÉ PAR dev_service_generator.py — NE PAS MODIFIER
import { notFound } from 'next/navigation'
import prisma from '@/lib/prisma'
import type { ProgressReport } from '@prisma/client'
import type { CreateProgressReportInput, UpdateProgressReportInput, SerializedProgressReport } from '@/lib/types'

const _serialize = (item: ProgressReport): SerializedProgressReport => {
  const { userId: _owner, ...rest } = item
  return ({
    ...rest,
  createdAt: rest.createdAt.toISOString(),
  updatedAt: rest.updatedAt.toISOString(),
  }) as SerializedProgressReport
}

export const progressReportService = {
  getAll: async (userId: string, page: number = 1, pageSize: number = 20): Promise<SerializedProgressReport[]> => {
    const items = await prisma.progressReport.findMany({ where: { userId }, select: { id: true, content: true, studentId: true, createdAt: true, updatedAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedProgressReport[]
  },

  getAllAsAdmin: async (page: number = 1, pageSize: number = 20): Promise<SerializedProgressReport[]> => {
    const items = await prisma.progressReport.findMany({ select: { id: true, content: true, studentId: true, createdAt: true, updatedAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedProgressReport[]
  },

  getByIdAsAdmin: async (id: string): Promise<SerializedProgressReport> => {
    const item = await prisma.progressReport.findFirst({ where: { id } })
    if (!item) notFound()
    return _serialize(item)
  },

  getById: async (userId: string, id: string): Promise<SerializedProgressReport> => {
    const item = await prisma.progressReport.findFirst({ where: { id, userId } })
    if (!item) notFound()
    return _serialize(item)
  },

  create: async (userId: string, data: CreateProgressReportInput): Promise<SerializedProgressReport> => {
    const result = await prisma.progressReport.create({
      data: { ...data, userId }
    })
    return _serialize(result)
  },

  update: async (userId: string, id: string, data: UpdateProgressReportInput): Promise<SerializedProgressReport> => {
    const result = await prisma.progressReport.update({
      where: { id, userId },
      data: { ...data }
    })
    return _serialize(result)
  },

  delete: async (userId: string, id: string): Promise<void> => {
    await prisma.progressReport.delete({ where: { id, userId } })
  },

  getAllWithRelations: async (userId: string, page: number = 1, pageSize: number = 20): Promise<SerializedProgressReport[]> => {
    const items = await prisma.progressReport.findMany({ where: { userId }, select: { id: true, content: true, studentId: true, createdAt: true, updatedAt: true, student: { select: { id: true } } }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedProgressReport[]
  },

  getByIdWithRelations: async (userId: string, id: string): Promise<SerializedProgressReport> => {
    const item = await prisma.progressReport.findFirst({ where: { id, userId }, select: { id: true, content: true, studentId: true, createdAt: true, updatedAt: true, student: { select: { id: true } } } })
    if (!item) notFound()
    return (item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() }))(item) as SerializedProgressReport
  },

  getByIdWithRelationsAsAdmin: async (id: string): Promise<SerializedProgressReport> => {
    const item = await prisma.progressReport.findFirst({ where: { id }, select: { id: true, content: true, studentId: true, createdAt: true, updatedAt: true, student: { select: { id: true } } } })
    if (!item) notFound()
    return (item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() }))(item) as SerializedProgressReport
  },
}
