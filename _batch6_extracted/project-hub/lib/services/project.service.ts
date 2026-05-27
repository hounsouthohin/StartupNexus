// AUTO-GÉNÉRÉ PAR dev_service_generator.py — NE PAS MODIFIER
import { notFound } from 'next/navigation'
import prisma from '@/lib/prisma'
import type { Project } from '@prisma/client'
import type { CreateProjectInput, UpdateProjectInput, SerializedProject } from '@/lib/types'

const _serialize = (item: Project): SerializedProject => {
  const { userId: _owner, ...rest } = item
  return ({
    ...rest,
  createdAt: rest.createdAt.toISOString(),
  }) as SerializedProject
}

export const projectService = {
  getAll: async (userId: string, page: number = 1, pageSize: number = 20): Promise<SerializedProject[]> => {
    const items = await prisma.project.findMany({ where: { userId }, select: { id: true, title: true, description: true, status: true, createdAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, createdAt: item.createdAt.toISOString() })) as SerializedProject[]
  },

  getById: async (userId: string, id: string): Promise<SerializedProject> => {
    const item = await prisma.project.findFirst({ where: { id, userId } })
    if (!item) notFound()
    return _serialize(item)
  },

  getAllWithRelations: async (userId: string): Promise<SerializedProject[]> => {
    const items = await prisma.project.findMany({ where: { userId }, select: { id: true, title: true, description: true, status: true, createdAt: true, tasks: { select: { id: true, title: true, description: true } } }, orderBy: { createdAt: 'desc' }, take: 20, skip: 0 })
    return items.map(item => ({ ...item, createdAt: item.createdAt.toISOString() })) as SerializedProject[]
  },

  getByIdWithRelations: async (userId: string, id: string): Promise<SerializedProject> => {
    const item = await prisma.project.findFirst({ where: { id, userId }, select: { id: true, title: true, description: true, status: true, createdAt: true, tasks: { select: { id: true, title: true, description: true } } } })
    if (!item) notFound()
    return (item => ({ ...item, createdAt: item.createdAt.toISOString() }))(item) as SerializedProject
  },

  create: async (userId: string, data: CreateProjectInput): Promise<Project> => {
    return prisma.project.create({
      data: { ...data, userId }
    })
  },

  update: async (userId: string, id: string, data: UpdateProjectInput): Promise<Project> => {
    return prisma.project.update({
      where: { id, userId },
      data: { ...data }
    })
  },

  delete: async (userId: string, id: string): Promise<void> => {
    await prisma.project.delete({ where: { id, userId } })
  },
}
