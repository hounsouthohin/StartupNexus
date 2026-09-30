// AUTO-GÉNÉRÉ PAR dev_service_generator.py — NE PAS MODIFIER
import { notFound } from 'next/navigation'
import prisma from '@/lib/prisma'
import type { Tag } from '@prisma/client'
import type { CreateTagInput, UpdateTagInput, SerializedTag } from '@/lib/types'

const _serialize = (item: Tag): SerializedTag => {
  const { userId: _owner, ...rest } = item
  return ({
    ...rest,
  createdAt: rest.createdAt.toISOString(),
  updatedAt: rest.updatedAt.toISOString(),
  }) as SerializedTag
}

export const tagService = {
  getAll: async (userId: string, page: number = 1, pageSize: number = 20): Promise<SerializedTag[]> => {
    const items = await prisma.tag.findMany({ where: { userId }, select: { id: true, name: true, createdAt: true, updatedAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedTag[]
  },

  getById: async (userId: string, id: string): Promise<SerializedTag> => {
    const item = await prisma.tag.findFirst({ where: { id, userId } })
    if (!item) notFound()
    return _serialize(item)
  },

  create: async (userId: string, data: CreateTagInput): Promise<SerializedTag> => {
    const { recipeIds, ...rest } = data
    const _valid_recipeIds = recipeIds && recipeIds.length
      ? (await prisma.recipe.findMany({ where: { id: { in: recipeIds }, userId: userId }, select: { id: true } })).map(_r => _r.id)
      : []
    const result = await prisma.tag.create({
      data: { ...rest, userId, ...(_valid_recipeIds.length ? { recipes: { connect: _valid_recipeIds.map(_id => ({ id: _id })) } } : {}) }
    })
    return _serialize(result)
  },

  update: async (userId: string, id: string, data: UpdateTagInput): Promise<SerializedTag> => {
    const { recipeIds, ...rest } = data
    const _valid_recipeIds = recipeIds && recipeIds.length
      ? (await prisma.recipe.findMany({ where: { id: { in: recipeIds }, userId: userId }, select: { id: true } })).map(_r => _r.id)
      : []
    const result = await prisma.tag.update({
      where: { id, userId },
      data: { ...rest, ...(recipeIds !== undefined ? { recipes: { set: _valid_recipeIds.map(_id => ({ id: _id })) } } : {}) }
    })
    return _serialize(result)
  },

  delete: async (userId: string, id: string): Promise<void> => {
    await prisma.tag.delete({ where: { id, userId } })
  },

  getAllWithRelations: async (userId: string, page: number = 1, pageSize: number = 20): Promise<SerializedTag[]> => {
    const items = await prisma.tag.findMany({ where: { userId }, select: { id: true, name: true, createdAt: true, updatedAt: true, recipes: { select: { id: true, title: true, instructions: true, preparationTime: true, difficulty: true } } }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedTag[]
  },

  getByIdWithRelations: async (userId: string, id: string): Promise<SerializedTag> => {
    const item = await prisma.tag.findFirst({ where: { id, userId }, select: { id: true, name: true, createdAt: true, updatedAt: true, recipes: { select: { id: true, title: true, instructions: true, preparationTime: true, difficulty: true } } } })
    if (!item) notFound()
    return (item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() }))(item) as SerializedTag
  },
}
