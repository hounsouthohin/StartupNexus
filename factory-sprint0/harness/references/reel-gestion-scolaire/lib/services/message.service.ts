// AUTO-GÉNÉRÉ PAR dev_service_generator.py — NE PAS MODIFIER
import { notFound } from 'next/navigation'
import prisma from '@/lib/prisma'
import type { Message } from '@prisma/client'
import type { CreateMessageInput, UpdateMessageInput, SerializedMessage } from '@/lib/types'

const _serialize = (item: Message): SerializedMessage => {
  const { userId: _owner, ...rest } = item
  return ({
    ...rest,
  createdAt: rest.createdAt.toISOString(),
  updatedAt: rest.updatedAt.toISOString(),
  }) as SerializedMessage
}

export const messageService = {
  getAll: async (userId: string, page: number = 1, pageSize: number = 20): Promise<SerializedMessage[]> => {
    const items = await prisma.message.findMany({ where: { userId }, select: { id: true, content: true, senderId: true, receiverId: true, createdAt: true, updatedAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedMessage[]
  },

  getAllAsAdmin: async (page: number = 1, pageSize: number = 20): Promise<SerializedMessage[]> => {
    const items = await prisma.message.findMany({ select: { id: true, content: true, senderId: true, receiverId: true, createdAt: true, updatedAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedMessage[]
  },

  getByIdAsAdmin: async (id: string): Promise<SerializedMessage> => {
    const item = await prisma.message.findFirst({ where: { id } })
    if (!item) notFound()
    return _serialize(item)
  },

  getById: async (userId: string, id: string): Promise<SerializedMessage> => {
    const item = await prisma.message.findFirst({ where: { id, userId } })
    if (!item) notFound()
    return _serialize(item)
  },

  create: async (userId: string, data: CreateMessageInput): Promise<SerializedMessage> => {
    const result = await prisma.message.create({
      data: { ...data, userId }
    })
    return _serialize(result)
  },

  update: async (userId: string, id: string, data: UpdateMessageInput): Promise<SerializedMessage> => {
    const result = await prisma.message.update({
      where: { id, userId },
      data: { ...data }
    })
    return _serialize(result)
  },

  delete: async (userId: string, id: string): Promise<void> => {
    await prisma.message.delete({ where: { id, userId } })
  },
}
