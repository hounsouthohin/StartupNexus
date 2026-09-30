// AUTO-GÉNÉRÉ PAR dev_service_generator.py — NE PAS MODIFIER
import { notFound } from 'next/navigation'
import prisma from '@/lib/prisma'
import type { Category } from '@prisma/client'
import type { CreateCategoryInput, UpdateCategoryInput, SerializedCategory } from '@/lib/types'

const _serialize = (item: Category): SerializedCategory => {
  const { userId: _owner, ...rest } = item
  return ({
    ...rest,
  createdAt: rest.createdAt.toISOString(),
  updatedAt: rest.updatedAt.toISOString(),
  }) as SerializedCategory
}

export const categoryService = {
  getAll: async (userId: string, page: number = 1, pageSize: number = 20): Promise<SerializedCategory[]> => {
    const items = await prisma.category.findMany({ where: { userId }, select: { id: true, name: true, description: true, createdAt: true, updatedAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedCategory[]
  },

  getById: async (userId: string, id: string): Promise<SerializedCategory> => {
    const item = await prisma.category.findFirst({ where: { id, userId } })
    if (!item) notFound()
    return _serialize(item)
  },

  create: async (userId: string, data: CreateCategoryInput): Promise<SerializedCategory> => {
    const result = await prisma.category.create({
      data: { ...data, userId }
    })
    return _serialize(result)
  },

  update: async (userId: string, id: string, data: UpdateCategoryInput): Promise<SerializedCategory> => {
    const result = await prisma.category.update({
      where: { id, userId },
      data: { ...data }
    })
    return _serialize(result)
  },

  delete: async (userId: string, id: string): Promise<void> => {
    await prisma.category.delete({ where: { id, userId } })
  },

  getAllWithRelations: async (userId: string, page: number = 1, pageSize: number = 20): Promise<SerializedCategory[]> => {
    const items = await prisma.category.findMany({ where: { userId }, select: { id: true, name: true, description: true, createdAt: true, updatedAt: true, subscriptions: { select: { id: true, name: true, nextBillingDate: true, status: true } } }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString(), subscriptions: (item.subscriptions ?? []).map(c => ({ ...c, nextBillingDate: c.nextBillingDate.toISOString() })) })) as SerializedCategory[]
  },

  getByIdWithRelations: async (userId: string, id: string): Promise<SerializedCategory> => {
    const item = await prisma.category.findFirst({ where: { id, userId }, select: { id: true, name: true, description: true, createdAt: true, updatedAt: true, subscriptions: { select: { id: true, name: true, nextBillingDate: true, status: true } } } })
    if (!item) notFound()
    return (item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString(), subscriptions: (item.subscriptions ?? []).map(c => ({ ...c, nextBillingDate: c.nextBillingDate.toISOString() })) }))(item) as SerializedCategory
  },
}
