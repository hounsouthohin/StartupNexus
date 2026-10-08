// AUTO-GÉNÉRÉ PAR dev_service_generator.py — NE PAS MODIFIER
import { notFound } from 'next/navigation'
import prisma from '@/lib/prisma'
import type { Textbook } from '@prisma/client'
import type { CreateTextbookInput, UpdateTextbookInput, SerializedTextbook } from '@/lib/types'

const _serialize = (item: Textbook): SerializedTextbook => {
  const { userId: _owner, ...rest } = item
  return ({
    ...rest,
  createdAt: rest.createdAt.toISOString(),
  updatedAt: rest.updatedAt.toISOString(),
  }) as SerializedTextbook
}

export const textbookService = {
  getAll: async (userId: string, page: number = 1, pageSize: number = 20): Promise<SerializedTextbook[]> => {
    const items = await prisma.textbook.findMany({ where: { userId }, select: { id: true, title: true, content: true, createdAt: true, updatedAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedTextbook[]
  },

  getAllAsAdmin: async (page: number = 1, pageSize: number = 20): Promise<SerializedTextbook[]> => {
    const items = await prisma.textbook.findMany({ select: { id: true, title: true, content: true, createdAt: true, updatedAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedTextbook[]
  },

  getByIdAsAdmin: async (id: string): Promise<SerializedTextbook> => {
    const item = await prisma.textbook.findFirst({ where: { id } })
    if (!item) notFound()
    return _serialize(item)
  },

  getById: async (userId: string, id: string): Promise<SerializedTextbook> => {
    const item = await prisma.textbook.findFirst({ where: { id, userId } })
    if (!item) notFound()
    return _serialize(item)
  },

  create: async (userId: string, data: CreateTextbookInput): Promise<SerializedTextbook> => {
    const result = await prisma.textbook.create({
      data: { ...data, userId }
    })
    return _serialize(result)
  },

  update: async (userId: string, id: string, data: UpdateTextbookInput): Promise<SerializedTextbook> => {
    const result = await prisma.textbook.update({
      where: { id, userId },
      data: { ...data }
    })
    return _serialize(result)
  },

  delete: async (userId: string, id: string): Promise<void> => {
    await prisma.textbook.delete({ where: { id, userId } })
  },
}
