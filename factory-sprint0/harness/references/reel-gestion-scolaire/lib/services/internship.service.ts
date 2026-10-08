// AUTO-GÉNÉRÉ PAR dev_service_generator.py — NE PAS MODIFIER
import { notFound } from 'next/navigation'
import prisma from '@/lib/prisma'
import type { Internship } from '@prisma/client'
import type { CreateInternshipInput, UpdateInternshipInput, SerializedInternship } from '@/lib/types'

const _serialize = (item: Internship): SerializedInternship => {
  const { userId: _owner, ...rest } = item
  return ({
    ...rest,
  createdAt: rest.createdAt.toISOString(),
  updatedAt: rest.updatedAt.toISOString(),
  }) as SerializedInternship
}

export const internshipService = {
  getAll: async (userId: string, page: number = 1, pageSize: number = 20): Promise<SerializedInternship[]> => {
    const items = await prisma.internship.findMany({ where: { userId }, select: { id: true, companyName: true, duration: true, studentId: true, createdAt: true, updatedAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedInternship[]
  },

  getAllAsAdmin: async (page: number = 1, pageSize: number = 20): Promise<SerializedInternship[]> => {
    const items = await prisma.internship.findMany({ select: { id: true, companyName: true, duration: true, studentId: true, createdAt: true, updatedAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedInternship[]
  },

  getByIdAsAdmin: async (id: string): Promise<SerializedInternship> => {
    const item = await prisma.internship.findFirst({ where: { id } })
    if (!item) notFound()
    return _serialize(item)
  },

  getById: async (userId: string, id: string): Promise<SerializedInternship> => {
    const item = await prisma.internship.findFirst({ where: { id, userId } })
    if (!item) notFound()
    return _serialize(item)
  },

  create: async (userId: string, data: CreateInternshipInput): Promise<SerializedInternship> => {
    const result = await prisma.internship.create({
      data: { ...data, userId }
    })
    return _serialize(result)
  },

  update: async (userId: string, id: string, data: UpdateInternshipInput): Promise<SerializedInternship> => {
    const result = await prisma.internship.update({
      where: { id, userId },
      data: { ...data }
    })
    return _serialize(result)
  },

  delete: async (userId: string, id: string): Promise<void> => {
    await prisma.internship.delete({ where: { id, userId } })
  },

  getAllWithRelations: async (userId: string, page: number = 1, pageSize: number = 20): Promise<SerializedInternship[]> => {
    const items = await prisma.internship.findMany({ where: { userId }, select: { id: true, companyName: true, duration: true, studentId: true, createdAt: true, updatedAt: true, student: { select: { id: true } } }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedInternship[]
  },

  getByIdWithRelations: async (userId: string, id: string): Promise<SerializedInternship> => {
    const item = await prisma.internship.findFirst({ where: { id, userId }, select: { id: true, companyName: true, duration: true, studentId: true, createdAt: true, updatedAt: true, student: { select: { id: true } } } })
    if (!item) notFound()
    return (item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() }))(item) as SerializedInternship
  },

  getByIdWithRelationsAsAdmin: async (id: string): Promise<SerializedInternship> => {
    const item = await prisma.internship.findFirst({ where: { id }, select: { id: true, companyName: true, duration: true, studentId: true, createdAt: true, updatedAt: true, student: { select: { id: true } } } })
    if (!item) notFound()
    return (item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() }))(item) as SerializedInternship
  },
}
