// AUTO-GÉNÉRÉ PAR dev_service_generator.py — NE PAS MODIFIER
import { notFound } from 'next/navigation'
import prisma from '@/lib/prisma'
import type { News } from '@prisma/client'
import type { CreateNewsInput, UpdateNewsInput, SerializedNews } from '@/lib/types'

const _serialize = (item: News): SerializedNews => {
  const { userId: _owner, ...rest } = item
  return ({
    ...rest,
  createdAt: rest.createdAt.toISOString(),
  updatedAt: rest.updatedAt.toISOString(),
  }) as SerializedNews
}

export const newsService = {
  getAll: async (userId: string, page: number = 1, pageSize: number = 20): Promise<SerializedNews[]> => {
    const items = await prisma.news.findMany({ where: { userId }, select: { id: true, title: true, content: true, createdAt: true, updatedAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedNews[]
  },

  getAllAsAdmin: async (page: number = 1, pageSize: number = 20): Promise<SerializedNews[]> => {
    const items = await prisma.news.findMany({ select: { id: true, title: true, content: true, createdAt: true, updatedAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedNews[]
  },

  getByIdAsAdmin: async (id: string): Promise<SerializedNews> => {
    const item = await prisma.news.findFirst({ where: { id } })
    if (!item) notFound()
    return _serialize(item)
  },

  getById: async (userId: string, id: string): Promise<SerializedNews> => {
    const item = await prisma.news.findFirst({ where: { id, userId } })
    if (!item) notFound()
    return _serialize(item)
  },

  create: async (userId: string, data: CreateNewsInput): Promise<SerializedNews> => {
    const result = await prisma.news.create({
      data: { ...data, userId }
    })
    return _serialize(result)
  },

  update: async (userId: string, id: string, data: UpdateNewsInput): Promise<SerializedNews> => {
    const result = await prisma.news.update({
      where: { id, userId },
      data: { ...data }
    })
    return _serialize(result)
  },

  delete: async (userId: string, id: string): Promise<void> => {
    await prisma.news.delete({ where: { id, userId } })
  },
}
