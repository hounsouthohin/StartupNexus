// AUTO-GÉNÉRÉ PAR dev_service_generator.py — NE PAS MODIFIER
import { notFound } from 'next/navigation'
import prisma from '@/lib/prisma'
import type { Recipe } from '@prisma/client'
import type { CreateRecipeInput, UpdateRecipeInput, SerializedRecipe } from '@/lib/types'

const _serialize = (item: Recipe): SerializedRecipe => {
  const { userId: _owner, ...rest } = item
  return ({
    ...rest,
  createdAt: rest.createdAt.toISOString(),
  updatedAt: rest.updatedAt.toISOString(),
  }) as SerializedRecipe
}

export const recipeService = {
  getAll: async (userId: string, page: number = 1, pageSize: number = 20): Promise<SerializedRecipe[]> => {
    const items = await prisma.recipe.findMany({ where: { userId }, select: { id: true, title: true, instructions: true, preparationTime: true, difficulty: true, published: true, slug: true, createdAt: true, updatedAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedRecipe[]
  },

  getById: async (userId: string, id: string): Promise<SerializedRecipe> => {
    const item = await prisma.recipe.findFirst({ where: { id, userId } })
    if (!item) notFound()
    return _serialize(item)
  },

  create: async (userId: string, data: CreateRecipeInput): Promise<SerializedRecipe> => {
    const _slugBase = String(data.title ?? '').toLowerCase().trim().normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '') || 'recipe'
    let _slug = _slugBase
    for (let _i = 2; await prisma.recipe.findUnique({ where: { slug: _slug }, select: { id: true } }); _i++) { _slug = `${_slugBase}-${_i}` }
    const { tagIds, ...rest } = data
    const _valid_tagIds = tagIds && tagIds.length
      ? (await prisma.tag.findMany({ where: { id: { in: tagIds }, userId: userId }, select: { id: true } })).map(_r => _r.id)
      : []
    const result = await prisma.recipe.create({
      data: { ...rest, userId, slug: _slug, ...(_valid_tagIds.length ? { tags: { connect: _valid_tagIds.map(_id => ({ id: _id })) } } : {}) }
    })
    return _serialize(result)
  },

  update: async (userId: string, id: string, data: UpdateRecipeInput): Promise<SerializedRecipe> => {
    const { tagIds, ...rest } = data
    const _valid_tagIds = tagIds && tagIds.length
      ? (await prisma.tag.findMany({ where: { id: { in: tagIds }, userId: userId }, select: { id: true } })).map(_r => _r.id)
      : []
    const result = await prisma.recipe.update({
      where: { id, userId },
      data: { ...rest, ...(tagIds !== undefined ? { tags: { set: _valid_tagIds.map(_id => ({ id: _id })) } } : {}) }
    })
    return _serialize(result)
  },

  delete: async (userId: string, id: string): Promise<void> => {
    await prisma.recipe.delete({ where: { id, userId } })
  },

  getPublicById: async (id: string): Promise<SerializedRecipe> => {
    const item = await prisma.recipe.findUnique({ where: { id, published: true } })
    if (!item) notFound()
    return _serialize(item)
  },

  getPublicAll: async (page: number = 1, pageSize: number = 20): Promise<SerializedRecipe[]> => {
    const items = await prisma.recipe.findMany({ where: { published: true }, select: { id: true, title: true, instructions: true, preparationTime: true, difficulty: true, published: true, slug: true, createdAt: true, updatedAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedRecipe[]
  },

  getAllWithRelations: async (userId: string, page: number = 1, pageSize: number = 20): Promise<SerializedRecipe[]> => {
    const items = await prisma.recipe.findMany({ where: { userId }, select: { id: true, title: true, instructions: true, preparationTime: true, difficulty: true, published: true, slug: true, createdAt: true, updatedAt: true, tags: { select: { id: true, name: true } } }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedRecipe[]
  },

  getByIdWithRelations: async (userId: string, id: string): Promise<SerializedRecipe> => {
    const item = await prisma.recipe.findFirst({ where: { id, userId }, select: { id: true, title: true, instructions: true, preparationTime: true, difficulty: true, published: true, slug: true, createdAt: true, updatedAt: true, tags: { select: { id: true, name: true } } } })
    if (!item) notFound()
    return (item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() }))(item) as SerializedRecipe
  },

  getPublicByIdWithRelations: async (id: string): Promise<SerializedRecipe> => {
    const item = await prisma.recipe.findUnique({ where: { id, published: true }, select: { id: true, title: true, instructions: true, preparationTime: true, difficulty: true, published: true, slug: true, createdAt: true, updatedAt: true, tags: { select: { id: true, name: true } } } })
    if (!item) notFound()
    return (item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() }))(item) as SerializedRecipe
  },

  getBySlug: async (slug: string): Promise<SerializedRecipe> => {
    const item = await prisma.recipe.findUnique({ where: { slug, published: true } })
    if (!item) notFound()
    return _serialize(item)
  },

  getBySlugOwned: async (userId: string, slug: string): Promise<SerializedRecipe> => {
    const item = await prisma.recipe.findFirst({ where: { slug, userId }, select: { id: true, title: true, instructions: true, preparationTime: true, difficulty: true, published: true, slug: true, createdAt: true, updatedAt: true, tags: { select: { id: true, name: true } } } })
    if (!item) notFound()
    return (item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() }))(item) as SerializedRecipe
  },

  getBySlugWithRelations: async (slug: string): Promise<SerializedRecipe> => {
    const item = await prisma.recipe.findUnique({ where: { slug, published: true }, select: { id: true, title: true, instructions: true, preparationTime: true, difficulty: true, published: true, slug: true, createdAt: true, updatedAt: true, tags: { select: { id: true, name: true } } } })
    if (!item) notFound()
    return (item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() }))(item) as SerializedRecipe
  },
}
