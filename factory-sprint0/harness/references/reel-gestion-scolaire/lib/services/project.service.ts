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
  updatedAt: rest.updatedAt.toISOString(),
  }) as SerializedProject
}

export const projectService = {
  getAll: async (userId: string, page: number = 1, pageSize: number = 20): Promise<SerializedProject[]> => {
    const items = await prisma.project.findMany({ where: { userId }, select: { id: true, title: true, description: true, studentId: true, createdAt: true, updatedAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedProject[]
  },

  getAllAsAdmin: async (page: number = 1, pageSize: number = 20): Promise<SerializedProject[]> => {
    const items = await prisma.project.findMany({ select: { id: true, title: true, description: true, studentId: true, createdAt: true, updatedAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedProject[]
  },

  getByIdAsAdmin: async (id: string): Promise<SerializedProject> => {
    const item = await prisma.project.findFirst({ where: { id } })
    if (!item) notFound()
    return _serialize(item)
  },

  getById: async (userId: string, id: string): Promise<SerializedProject> => {
    const item = await prisma.project.findFirst({ where: { id, userId } })
    if (!item) notFound()
    return _serialize(item)
  },

  create: async (userId: string, data: CreateProjectInput): Promise<SerializedProject> => {
    const result = await prisma.project.create({
      data: { ...data, userId }
    })
    return _serialize(result)
  },

  update: async (userId: string, id: string, data: UpdateProjectInput): Promise<SerializedProject> => {
    const result = await prisma.project.update({
      where: { id, userId },
      data: { ...data }
    })
    return _serialize(result)
  },

  delete: async (userId: string, id: string): Promise<void> => {
    await prisma.project.delete({ where: { id, userId } })
  },

  getAllWithRelations: async (userId: string, page: number = 1, pageSize: number = 20): Promise<SerializedProject[]> => {
    const items = await prisma.project.findMany({ where: { userId }, select: { id: true, title: true, description: true, studentId: true, createdAt: true, updatedAt: true, student: { select: { id: true } } }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedProject[]
  },

  getByIdWithRelations: async (userId: string, id: string): Promise<SerializedProject> => {
    const item = await prisma.project.findFirst({ where: { id, userId }, select: { id: true, title: true, description: true, studentId: true, createdAt: true, updatedAt: true, student: { select: { id: true } } } })
    if (!item) notFound()
    return (item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() }))(item) as SerializedProject
  },

  getByIdWithRelationsAsAdmin: async (id: string): Promise<SerializedProject> => {
    const item = await prisma.project.findFirst({ where: { id }, select: { id: true, title: true, description: true, studentId: true, createdAt: true, updatedAt: true, student: { select: { id: true } } } })
    if (!item) notFound()
    return (item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() }))(item) as SerializedProject
  },
}
