// AUTO-GÉNÉRÉ PAR dev_service_generator.py — NE PAS MODIFIER
import { notFound } from 'next/navigation'
import prisma from '@/lib/prisma'
import type { Post } from '@prisma/client'
import type { CreatePostInput, UpdatePostInput, SerializedPost } from '@/lib/types'

const _serialize = (item: Post): SerializedPost => {
  const { authorId: _owner, ...rest } = item
  return ({
    ...rest,
  createdAt: rest.createdAt.toISOString(),
  }) as SerializedPost
}

export const postService = {
  getAll: async (authorId: string, page: number = 1, pageSize: number = 20): Promise<SerializedPost[]> => {
    const items = await prisma.post.findMany({ where: { authorId }, select: { id: true, title: true, excerpt: true, published: true, categoryId: true, createdAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, createdAt: item.createdAt.toISOString() })) as SerializedPost[]
  },

  getById: async (authorId: string, id: string): Promise<SerializedPost> => {
    const item = await prisma.post.findFirst({ where: { id, authorId } })
    if (!item) notFound()
    return _serialize(item)
  },

  getPublicById: async (id: string): Promise<SerializedPost> => {
    const item = await prisma.post.findUnique({ where: { id } })
    if (!item) notFound()
    return _serialize(item)
  },

  getPublicAll: async (): Promise<SerializedPost[]> => {
    const items = await prisma.post.findMany({ select: { id: true, title: true, excerpt: true, published: true, categoryId: true, createdAt: true }, orderBy: { createdAt: 'desc' }, take: 50, skip: 0 })
    return items.map(item => ({ ...item, createdAt: item.createdAt.toISOString() })) as SerializedPost[]
  },

  getAllWithRelations: async (authorId: string): Promise<SerializedPost[]> => {
    const items = await prisma.post.findMany({ where: { authorId }, select: { id: true, title: true, excerpt: true, published: true, categoryId: true, createdAt: true, category: { select: { id: true, name: true } } }, orderBy: { createdAt: 'desc' }, take: 20, skip: 0 })
    return items.map(item => ({ ...item, createdAt: item.createdAt.toISOString() })) as SerializedPost[]
  },

  getByIdWithRelations: async (authorId: string, id: string): Promise<SerializedPost> => {
    const item = await prisma.post.findFirst({ where: { id, authorId }, select: { id: true, title: true, excerpt: true, published: true, categoryId: true, createdAt: true, category: { select: { id: true, name: true } } } })
    if (!item) notFound()
    return (item => ({ ...item, createdAt: item.createdAt.toISOString() }))(item) as SerializedPost
  },

  getPublicByIdWithRelations: async (id: string): Promise<SerializedPost> => {
    const item = await prisma.post.findUnique({ where: { id }, select: { id: true, title: true, excerpt: true, published: true, categoryId: true, createdAt: true, category: { select: { id: true, name: true } } } })
    if (!item) notFound()
    return (item => ({ ...item, createdAt: item.createdAt.toISOString() }))(item) as SerializedPost
  },

  create: async (authorId: string, data: CreatePostInput): Promise<Post> => {
    return prisma.post.create({
      data: { ...data, authorId }
    })
  },

  update: async (authorId: string, id: string, data: UpdatePostInput): Promise<Post> => {
    return prisma.post.update({
      where: { id, authorId },
      data: { ...data }
    })
  },

  delete: async (authorId: string, id: string): Promise<void> => {
    await prisma.post.delete({ where: { id, authorId } })
  },
}
