// AUTO-GÉNÉRÉ PAR dev_service_generator.py — NE PAS MODIFIER
import { notFound } from 'next/navigation'
import prisma from '@/lib/prisma'
import type { Course } from '@prisma/client'
import type { CreateCourseInput, UpdateCourseInput, SerializedCourse } from '@/lib/types'

const _serialize = (item: Course): SerializedCourse => {
  const rest = item
  return ({
    ...rest,
  schedule: rest.schedule.toISOString(),
  createdAt: rest.createdAt.toISOString(),
  updatedAt: rest.updatedAt.toISOString(),
  }) as SerializedCourse
}

export const courseService = {
  getAll: async (userId: string, page: number = 1, pageSize: number = 20): Promise<SerializedCourse[]> => {
    const items = await prisma.course.findMany({ where: {  }, select: { id: true, title: true, description: true, schedule: true, createdAt: true, updatedAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, schedule: item.schedule.toISOString(), createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedCourse[]
  },

  getById: async (userId: string, id: string): Promise<SerializedCourse> => {
    const item = await prisma.course.findFirst({ where: { id } })
    if (!item) notFound()
    return _serialize(item)
  },

  create: async (userId: string, data: CreateCourseInput): Promise<SerializedCourse> => {
    const result = await prisma.course.create({
      data: { ...data }
    })
    return _serialize(result)
  },

  update: async (userId: string, id: string, data: UpdateCourseInput): Promise<SerializedCourse> => {
    const result = await prisma.course.update({
      where: { id },
      data: { ...data }
    })
    return _serialize(result)
  },

  delete: async (userId: string, id: string): Promise<void> => {
    await prisma.course.delete({ where: { id } })
  },

  getPublicById: async (id: string): Promise<SerializedCourse> => {
    const item = await prisma.course.findUnique({ where: { id } })
    if (!item) notFound()
    return _serialize(item)
  },

  getPublicAll: async (page: number = 1, pageSize: number = 20): Promise<SerializedCourse[]> => {
    const items = await prisma.course.findMany({ select: { id: true, title: true, description: true, schedule: true, createdAt: true, updatedAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, schedule: item.schedule.toISOString(), createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedCourse[]
  },

  getAllWithRelations: async (userId: string, page: number = 1, pageSize: number = 20): Promise<SerializedCourse[]> => {
    const items = await prisma.course.findMany({ where: { userId }, select: { id: true, title: true, description: true, schedule: true, createdAt: true, updatedAt: true, reservations: { select: { id: true } } }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, schedule: item.schedule.toISOString(), createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedCourse[]
  },

  getByIdWithRelations: async (userId: string, id: string): Promise<SerializedCourse> => {
    const item = await prisma.course.findFirst({ where: { id, userId }, select: { id: true, title: true, description: true, schedule: true, createdAt: true, updatedAt: true, reservations: { select: { id: true } } } })
    if (!item) notFound()
    return (item => ({ ...item, schedule: item.schedule.toISOString(), createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() }))(item) as SerializedCourse
  },

  getPublicByIdWithRelations: async (id: string): Promise<SerializedCourse> => {
    const item = await prisma.course.findUnique({ where: { id }, select: { id: true, title: true, description: true, schedule: true, createdAt: true, updatedAt: true, reservations: { select: { id: true } } } })
    if (!item) notFound()
    return (item => ({ ...item, schedule: item.schedule.toISOString(), createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() }))(item) as SerializedCourse
  },
}
