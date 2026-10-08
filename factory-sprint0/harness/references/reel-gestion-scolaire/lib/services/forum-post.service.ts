// AUTO-GÉNÉRÉ PAR dev_service_generator.py — NE PAS MODIFIER
import { notFound } from 'next/navigation'
import prisma from '@/lib/prisma'
import type { ForumPost } from '@prisma/client'
import type { CreateForumPostInput, UpdateForumPostInput, SerializedForumPost } from '@/lib/types'

const _serialize = (item: ForumPost): SerializedForumPost => {
  const { userId: _owner, ...rest } = item
  return ({
    ...rest,
  createdAt: rest.createdAt.toISOString(),
  updatedAt: rest.updatedAt.toISOString(),
  }) as SerializedForumPost
}

export const forumPostService = {
  getAll: async (userId: string, page: number = 1, pageSize: number = 20): Promise<SerializedForumPost[]> => {
    const items = await prisma.forumPost.findMany({ where: { userId }, select: { id: true, title: true, content: true, createdAt: true, updatedAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedForumPost[]
  },

  getAllAsAdmin: async (page: number = 1, pageSize: number = 20): Promise<SerializedForumPost[]> => {
    const items = await prisma.forumPost.findMany({ select: { id: true, title: true, content: true, createdAt: true, updatedAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedForumPost[]
  },

  getByIdAsAdmin: async (id: string): Promise<SerializedForumPost> => {
    const item = await prisma.forumPost.findFirst({ where: { id } })
    if (!item) notFound()
    return _serialize(item)
  },

  getById: async (userId: string, id: string): Promise<SerializedForumPost> => {
    const item = await prisma.forumPost.findFirst({ where: { id, userId } })
    if (!item) notFound()
    return _serialize(item)
  },

  create: async (userId: string, data: CreateForumPostInput): Promise<SerializedForumPost> => {
    const result = await prisma.forumPost.create({
      data: { ...data, userId }
    })
    return _serialize(result)
  },

  update: async (userId: string, id: string, data: UpdateForumPostInput): Promise<SerializedForumPost> => {
    const result = await prisma.forumPost.update({
      where: { id, userId },
      data: { ...data }
    })
    return _serialize(result)
  },

  delete: async (userId: string, id: string): Promise<void> => {
    await prisma.forumPost.delete({ where: { id, userId } })
  },
}
