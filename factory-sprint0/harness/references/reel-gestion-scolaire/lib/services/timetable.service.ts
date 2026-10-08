// AUTO-GÉNÉRÉ PAR dev_service_generator.py — NE PAS MODIFIER
import { notFound } from 'next/navigation'
import prisma from '@/lib/prisma'
import type { Timetable } from '@prisma/client'
import type { CreateTimetableInput, UpdateTimetableInput, SerializedTimetable } from '@/lib/types'

const _serialize = (item: Timetable): SerializedTimetable => {
  const { userId: _owner, ...rest } = item
  return ({
    ...rest,
  createdAt: rest.createdAt.toISOString(),
  updatedAt: rest.updatedAt.toISOString(),
  }) as SerializedTimetable
}

export const timetableService = {
  getAll: async (userId: string, page: number = 1, pageSize: number = 20): Promise<SerializedTimetable[]> => {
    const items = await prisma.timetable.findMany({ where: { userId }, select: { id: true, schedule: true, createdAt: true, updatedAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedTimetable[]
  },

  getAllAsAdmin: async (page: number = 1, pageSize: number = 20): Promise<SerializedTimetable[]> => {
    const items = await prisma.timetable.findMany({ select: { id: true, schedule: true, createdAt: true, updatedAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedTimetable[]
  },

  getByIdAsAdmin: async (id: string): Promise<SerializedTimetable> => {
    const item = await prisma.timetable.findFirst({ where: { id } })
    if (!item) notFound()
    return _serialize(item)
  },

  getById: async (userId: string, id: string): Promise<SerializedTimetable> => {
    const item = await prisma.timetable.findFirst({ where: { id, userId } })
    if (!item) notFound()
    return _serialize(item)
  },

  create: async (userId: string, data: CreateTimetableInput): Promise<SerializedTimetable> => {
    const result = await prisma.timetable.create({
      data: { ...data, userId }
    })
    return _serialize(result)
  },

  update: async (userId: string, id: string, data: UpdateTimetableInput): Promise<SerializedTimetable> => {
    const result = await prisma.timetable.update({
      where: { id, userId },
      data: { ...data }
    })
    return _serialize(result)
  },

  delete: async (userId: string, id: string): Promise<void> => {
    await prisma.timetable.delete({ where: { id, userId } })
  },
}
