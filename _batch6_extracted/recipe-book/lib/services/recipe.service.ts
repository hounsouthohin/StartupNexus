// AUTO-GÉNÉRÉ PAR dev_service_generator.py — NE PAS MODIFIER
import { notFound } from 'next/navigation'
import prisma from '@/lib/prisma'
import type { Recipe } from '@prisma/client'
import type { CreateRecipeInput, UpdateRecipeInput, SerializedRecipe } from '@/lib/types'

const _serialize = (item: Recipe): SerializedRecipe => {
  const { authorId: _owner, ...rest } = item
  return ({
    ...rest,
  createdAt: rest.createdAt.toISOString(),
  }) as SerializedRecipe
}

export const recipeService = {
  getAll: async (authorId: string, page: number = 1, pageSize: number = 20): Promise<SerializedRecipe[]> => {
    const items = await prisma.recipe.findMany({ where: { authorId }, select: { id: true, title: true, description: true, slug: true, status: true, createdAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, createdAt: item.createdAt.toISOString() })) as SerializedRecipe[]
  },

  getPublished: async (): Promise<SerializedRecipe[]> => {
    const items = await prisma.recipe.findMany({ where: { status: 'published' }, select: { id: true, title: true, description: true, slug: true, status: true, createdAt: true }, orderBy: { createdAt: 'desc' }, take: 50, skip: 0 })
    return items.map(item => ({ ...item, createdAt: item.createdAt.toISOString() })) as SerializedRecipe[]
  },

  getById: async (authorId: string, id: string): Promise<SerializedRecipe> => {
    const item = await prisma.recipe.findFirst({ where: { id, authorId } })
    if (!item) notFound()
    return _serialize(item)
  },

  getPublicById: async (id: string): Promise<SerializedRecipe> => {
    const item = await prisma.recipe.findUnique({ where: { id } })
    if (!item) notFound()
    return _serialize(item)
  },

  getPublicAll: async (): Promise<SerializedRecipe[]> => {
    const items = await prisma.recipe.findMany({ where: { status: 'published' }, select: { id: true, title: true, description: true, slug: true, status: true, createdAt: true }, orderBy: { createdAt: 'desc' }, take: 50, skip: 0 })
    return items.map(item => ({ ...item, createdAt: item.createdAt.toISOString() })) as SerializedRecipe[]
  },

  getBySlug: async (slug: string): Promise<SerializedRecipe> => {
    const item = await prisma.recipe.findUnique({ where: { slug } })
    if (!item) notFound()
    return _serialize(item)
  },

  create: async (authorId: string, data: CreateRecipeInput): Promise<Recipe> => {
    return prisma.recipe.create({
      data: { ...data, authorId }
    })
  },

  update: async (authorId: string, id: string, data: UpdateRecipeInput): Promise<Recipe> => {
    return prisma.recipe.update({
      where: { id, authorId },
      data: { ...data }
    })
  },

  delete: async (authorId: string, id: string): Promise<void> => {
    await prisma.recipe.delete({ where: { id, authorId } })
  },
}
