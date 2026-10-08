// AUTO-GÉNÉRÉ PAR dev_service_generator.py — NE PAS MODIFIER
import { notFound } from 'next/navigation'
import prisma from '@/lib/prisma'
import type { Course } from '@prisma/client'
import type { CreateCourseInput, UpdateCourseInput, SerializedCourse } from '@/lib/types'

const _serialize = (item: Course): SerializedCourse => {
  const { userId: _owner, ...rest } = item
  return ({
    ...rest,
  createdAt: rest.createdAt.toISOString(),
  updatedAt: rest.updatedAt.toISOString(),
  }) as SerializedCourse
}

export const courseService = {
  getAll: async (userId: string, page: number = 1, pageSize: number = 20): Promise<SerializedCourse[]> => {
    const items = await prisma.course.findMany({ where: { userId }, select: { id: true, name: true, description: true, credits: true, coefficient: true, createdAt: true, updatedAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedCourse[]
  },

  getAllAsAdmin: async (page: number = 1, pageSize: number = 20): Promise<SerializedCourse[]> => {
    const items = await prisma.course.findMany({ select: { id: true, name: true, description: true, credits: true, coefficient: true, createdAt: true, updatedAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedCourse[]
  },

  getByIdAsAdmin: async (id: string): Promise<SerializedCourse> => {
    const item = await prisma.course.findFirst({ where: { id } })
    if (!item) notFound()
    return _serialize(item)
  },

  getById: async (userId: string, id: string): Promise<SerializedCourse> => {
    const item = await prisma.course.findFirst({ where: { id, userId } })
    if (!item) notFound()
    return _serialize(item)
  },

  create: async (userId: string, data: CreateCourseInput): Promise<SerializedCourse> => {
    const result = await prisma.course.create({
      data: { ...data, userId }
    })
    return _serialize(result)
  },

  update: async (userId: string, id: string, data: UpdateCourseInput): Promise<SerializedCourse> => {
    const result = await prisma.course.update({
      where: { id, userId },
      data: { ...data }
    })
    return _serialize(result)
  },

  delete: async (userId: string, id: string): Promise<void> => {
    await prisma.course.delete({ where: { id, userId } })
  },
}
