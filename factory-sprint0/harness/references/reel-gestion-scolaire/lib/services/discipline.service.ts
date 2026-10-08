// AUTO-GÉNÉRÉ PAR dev_service_generator.py — NE PAS MODIFIER
import { notFound } from 'next/navigation'
import prisma from '@/lib/prisma'
import type { Discipline } from '@prisma/client'
import type { CreateDisciplineInput, UpdateDisciplineInput, SerializedDiscipline } from '@/lib/types'

const _serialize = (item: Discipline): SerializedDiscipline => {
  const { userId: _owner, ...rest } = item
  return ({
    ...rest,
  createdAt: rest.createdAt.toISOString(),
  updatedAt: rest.updatedAt.toISOString(),
  }) as SerializedDiscipline
}

export const disciplineService = {
  getAll: async (userId: string, page: number = 1, pageSize: number = 20): Promise<SerializedDiscipline[]> => {
    const items = await prisma.discipline.findMany({ where: { userId }, select: { id: true, name: true, description: true, createdAt: true, updatedAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedDiscipline[]
  },

  getAllAsAdmin: async (page: number = 1, pageSize: number = 20): Promise<SerializedDiscipline[]> => {
    const items = await prisma.discipline.findMany({ select: { id: true, name: true, description: true, createdAt: true, updatedAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedDiscipline[]
  },

  getByIdAsAdmin: async (id: string): Promise<SerializedDiscipline> => {
    const item = await prisma.discipline.findFirst({ where: { id } })
    if (!item) notFound()
    return _serialize(item)
  },

  getById: async (userId: string, id: string): Promise<SerializedDiscipline> => {
    const item = await prisma.discipline.findFirst({ where: { id, userId } })
    if (!item) notFound()
    return _serialize(item)
  },

  create: async (userId: string, data: CreateDisciplineInput): Promise<SerializedDiscipline> => {
    const result = await prisma.discipline.create({
      data: { ...data, userId }
    })
    return _serialize(result)
  },

  update: async (userId: string, id: string, data: UpdateDisciplineInput): Promise<SerializedDiscipline> => {
    const result = await prisma.discipline.update({
      where: { id, userId },
      data: { ...data }
    })
    return _serialize(result)
  },

  delete: async (userId: string, id: string): Promise<void> => {
    await prisma.discipline.delete({ where: { id, userId } })
  },
}
