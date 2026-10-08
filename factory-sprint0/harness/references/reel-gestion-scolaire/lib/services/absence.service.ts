// AUTO-GÉNÉRÉ PAR dev_service_generator.py — NE PAS MODIFIER
import { notFound } from 'next/navigation'
import prisma from '@/lib/prisma'
import type { Absence } from '@prisma/client'
import type { CreateAbsenceInput, UpdateAbsenceInput, SerializedAbsence } from '@/lib/types'

const _serialize = (item: Absence): SerializedAbsence => {
  const { userId: _owner, ...rest } = item
  return ({
    ...rest,
  date: rest.date.toISOString(),
  createdAt: rest.createdAt.toISOString(),
  updatedAt: rest.updatedAt.toISOString(),
  }) as SerializedAbsence
}

export const absenceService = {
  getAll: async (userId: string, page: number = 1, pageSize: number = 20): Promise<SerializedAbsence[]> => {
    const items = await prisma.absence.findMany({ where: { userId }, select: { id: true, date: true, reason: true, studentId: true, createdAt: true, updatedAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, date: item.date.toISOString(), createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedAbsence[]
  },

  getAllAsAdmin: async (page: number = 1, pageSize: number = 20): Promise<SerializedAbsence[]> => {
    const items = await prisma.absence.findMany({ select: { id: true, date: true, reason: true, studentId: true, createdAt: true, updatedAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, date: item.date.toISOString(), createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedAbsence[]
  },

  getByIdAsAdmin: async (id: string): Promise<SerializedAbsence> => {
    const item = await prisma.absence.findFirst({ where: { id } })
    if (!item) notFound()
    return _serialize(item)
  },

  getById: async (userId: string, id: string): Promise<SerializedAbsence> => {
    const item = await prisma.absence.findFirst({ where: { id, userId } })
    if (!item) notFound()
    return _serialize(item)
  },

  create: async (userId: string, data: CreateAbsenceInput): Promise<SerializedAbsence> => {
    const result = await prisma.absence.create({
      data: { ...data, userId }
    })
    return _serialize(result)
  },

  update: async (userId: string, id: string, data: UpdateAbsenceInput): Promise<SerializedAbsence> => {
    const result = await prisma.absence.update({
      where: { id, userId },
      data: { ...data }
    })
    return _serialize(result)
  },

  delete: async (userId: string, id: string): Promise<void> => {
    await prisma.absence.delete({ where: { id, userId } })
  },

  getAllWithRelations: async (userId: string, page: number = 1, pageSize: number = 20): Promise<SerializedAbsence[]> => {
    const items = await prisma.absence.findMany({ where: { userId }, select: { id: true, date: true, reason: true, studentId: true, createdAt: true, updatedAt: true, student: { select: { id: true } } }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, date: item.date.toISOString(), createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedAbsence[]
  },

  getByIdWithRelations: async (userId: string, id: string): Promise<SerializedAbsence> => {
    const item = await prisma.absence.findFirst({ where: { id, userId }, select: { id: true, date: true, reason: true, studentId: true, createdAt: true, updatedAt: true, student: { select: { id: true } } } })
    if (!item) notFound()
    return (item => ({ ...item, date: item.date.toISOString(), createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() }))(item) as SerializedAbsence
  },

  getByIdWithRelationsAsAdmin: async (id: string): Promise<SerializedAbsence> => {
    const item = await prisma.absence.findFirst({ where: { id }, select: { id: true, date: true, reason: true, studentId: true, createdAt: true, updatedAt: true, student: { select: { id: true } } } })
    if (!item) notFound()
    return (item => ({ ...item, date: item.date.toISOString(), createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() }))(item) as SerializedAbsence
  },
}
