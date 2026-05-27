// AUTO-GÉNÉRÉ PAR dev_service_generator.py — NE PAS MODIFIER
import { notFound } from 'next/navigation'
import prisma from '@/lib/prisma'
import type { Comment } from '@prisma/client'
import type { CreateCommentInput, UpdateCommentInput, SerializedComment } from '@/lib/types'

const _serialize = (item: Comment): SerializedComment => {
  const { userId: _owner, ...rest } = item
  return ({
    ...rest,
  createdAt: rest.createdAt.toISOString(),
  }) as SerializedComment
}

export const commentService = {
  getAll: async (userId: string, page: number = 1, pageSize: number = 20): Promise<SerializedComment[]> => {
    const items = await prisma.comment.findMany({ where: { userId }, select: { id: true, content: true, taskId: true, createdAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, createdAt: item.createdAt.toISOString() })) as SerializedComment[]
  },

  getById: async (userId: string, id: string): Promise<SerializedComment> => {
    const item = await prisma.comment.findFirst({ where: { id, userId } })
    if (!item) notFound()
    return _serialize(item)
  },

  getAllWithRelations: async (userId: string): Promise<SerializedComment[]> => {
    const items = await prisma.comment.findMany({ where: { userId }, select: { id: true, content: true, taskId: true, createdAt: true, task: { select: { id: true, title: true, description: true } } }, orderBy: { createdAt: 'desc' }, take: 20, skip: 0 })
    return items.map(item => ({ ...item, createdAt: item.createdAt.toISOString() })) as SerializedComment[]
  },

  getByIdWithRelations: async (userId: string, id: string): Promise<SerializedComment> => {
    const item = await prisma.comment.findFirst({ where: { id, userId }, select: { id: true, content: true, taskId: true, createdAt: true, task: { select: { id: true, title: true, description: true } } } })
    if (!item) notFound()
    return (item => ({ ...item, createdAt: item.createdAt.toISOString() }))(item) as SerializedComment
  },

  create: async (userId: string, data: CreateCommentInput): Promise<Comment> => {
    return prisma.comment.create({
      data: { ...data, userId }
    })
  },

  update: async (userId: string, id: string, data: UpdateCommentInput): Promise<Comment> => {
    return prisma.comment.update({
      where: { id, userId },
      data: { ...data }
    })
  },

  delete: async (userId: string, id: string): Promise<void> => {
    await prisma.comment.delete({ where: { id, userId } })
  },
}
