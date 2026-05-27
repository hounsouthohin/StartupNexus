// AUTO-GÉNÉRÉ PAR dev_service_generator.py — NE PAS MODIFIER
import { notFound } from 'next/navigation'
import prisma from '@/lib/prisma'
import type { Task } from '@prisma/client'
import type { CreateTaskInput, UpdateTaskInput, SerializedTask } from '@/lib/types'

const _serialize = (item: Task): SerializedTask => {
  const { userId: _owner, ...rest } = item
  return ({
    ...rest,
  createdAt: rest.createdAt.toISOString(),
  }) as SerializedTask
}

export const taskService = {
  getAll: async (userId: string, page: number = 1, pageSize: number = 20): Promise<SerializedTask[]> => {
    const items = await prisma.task.findMany({ where: { userId }, select: { id: true, title: true, description: true, priority: true, status: true, projectId: true, createdAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, createdAt: item.createdAt.toISOString() })) as SerializedTask[]
  },

  getById: async (userId: string, id: string): Promise<SerializedTask> => {
    const item = await prisma.task.findFirst({ where: { id, userId } })
    if (!item) notFound()
    return _serialize(item)
  },

  getAllWithRelations: async (userId: string): Promise<SerializedTask[]> => {
    const items = await prisma.task.findMany({ where: { userId }, select: { id: true, title: true, description: true, priority: true, status: true, projectId: true, createdAt: true, project: { select: { id: true, title: true, description: true } }, comments: { select: { id: true, content: true } } }, orderBy: { createdAt: 'desc' }, take: 20, skip: 0 })
    return items.map(item => ({ ...item, createdAt: item.createdAt.toISOString() })) as SerializedTask[]
  },

  getByIdWithRelations: async (userId: string, id: string): Promise<SerializedTask> => {
    const item = await prisma.task.findFirst({ where: { id, userId }, select: { id: true, title: true, description: true, priority: true, status: true, projectId: true, createdAt: true, project: { select: { id: true, title: true, description: true } }, comments: { select: { id: true, content: true } } } })
    if (!item) notFound()
    return (item => ({ ...item, createdAt: item.createdAt.toISOString() }))(item) as SerializedTask
  },

  create: async (userId: string, data: CreateTaskInput): Promise<Task> => {
    return prisma.task.create({
      data: { ...data, userId }
    })
  },

  update: async (userId: string, id: string, data: UpdateTaskInput): Promise<Task> => {
    return prisma.task.update({
      where: { id, userId },
      data: { ...data }
    })
  },

  delete: async (userId: string, id: string): Promise<void> => {
    await prisma.task.delete({ where: { id, userId } })
  },
}
