// AUTO-GÉNÉRÉ PAR dev_service_generator.py — NE PAS MODIFIER
import { notFound } from 'next/navigation'
import prisma from '@/lib/prisma'
import type { Category } from '@prisma/client'
import type { CreateCategoryInput, UpdateCategoryInput, SerializedCategory } from '@/lib/types'

const _serialize = (item: Category): SerializedCategory => {
  const { authorId: _owner, ...rest } = item
  return ({
    ...rest,
  createdAt: rest.createdAt.toISOString(),
  }) as SerializedCategory
}

export const categoryService = {
  getAll: async (authorId: string, page: number = 1, pageSize: number = 20): Promise<SerializedCategory[]> => {
    const items = await prisma.category.findMany({ where: { authorId }, select: { id: true, name: true, createdAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, createdAt: item.createdAt.toISOString() })) as SerializedCategory[]
  },

  getById: async (authorId: string, id: string): Promise<SerializedCategory> => {
    const item = await prisma.category.findFirst({ where: { id, authorId } })
    if (!item) notFound()
    return _serialize(item)
  },

  create: async (authorId: string, data: CreateCategoryInput): Promise<Category> => {
    return prisma.category.create({
      data: { ...data, authorId }
    })
  },

  update: async (authorId: string, id: string, data: UpdateCategoryInput): Promise<Category> => {
    return prisma.category.update({
      where: { id, authorId },
      data: { ...data }
    })
  },

  delete: async (authorId: string, id: string): Promise<void> => {
    await prisma.category.delete({ where: { id, authorId } })
  },
}
