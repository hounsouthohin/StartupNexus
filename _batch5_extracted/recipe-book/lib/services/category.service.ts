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
  }) as SerializedCategory
}

export const categoryService = {
  getAll: async (userId: string, page: number = 1, pageSize: number = 20): Promise<SerializedCategory[]> => {
    const items = await prisma.category.findMany({ where: { userId }, select: { id: true, name: true, createdAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, createdAt: item.createdAt.toISOString() })) as SerializedCategory[]
  },

  getById: async (userId: string, id: string): Promise<SerializedCategory> => {
    const item = await prisma.category.findFirst({ where: { id, userId } })
    if (!item) notFound()
    return _serialize(item)
  },

  getAllWithRelations: async (userId: string): Promise<SerializedCategory[]> => {
    const items = await prisma.category.findMany({ where: { userId }, select: { id: true, name: true, createdAt: true, recipes: { select: { id: true, title: true, description: true } } }, orderBy: { createdAt: 'desc' }, take: 20, skip: 0 })
    return items.map(item => ({ ...item, createdAt: item.createdAt.toISOString() })) as SerializedCategory[]
  },

  getByIdWithRelations: async (userId: string, id: string): Promise<SerializedCategory> => {
    const item = await prisma.category.findFirst({ where: { id, userId }, select: { id: true, name: true, createdAt: true, recipes: { select: { id: true, title: true, description: true } } } })
    if (!item) notFound()
    return (item => ({ ...item, createdAt: item.createdAt.toISOString() }))(item) as SerializedCategory
  },

  create: async (userId: string, data: CreateCategoryInput): Promise<Category> => {
    return prisma.category.create({
      data: { ...data, userId }
    })
  },

  update: async (userId: string, id: string, data: UpdateCategoryInput): Promise<Category> => {
    return prisma.category.update({
      where: { id, userId },
      data: { ...data }
    })
  },

  delete: async (userId: string, id: string): Promise<void> => {
    await prisma.category.delete({ where: { id, userId } })
  },
}
