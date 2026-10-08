// AUTO-GÉNÉRÉ PAR dev_service_generator.py — NE PAS MODIFIER
import { notFound } from 'next/navigation'
import prisma from '@/lib/prisma'
import type { Reservation } from '@prisma/client'
import type { CreateReservationInput, UpdateReservationInput, SerializedReservation } from '@/lib/types'

const _serialize = (item: Reservation): SerializedReservation => {
  const { courseId: _owner, ...rest } = item
  return ({
    ...rest,
  createdAt: rest.createdAt.toISOString(),
  updatedAt: rest.updatedAt.toISOString(),
  }) as SerializedReservation
}

export const reservationService = {
  getAll: async (courseId: string, page: number = 1, pageSize: number = 20): Promise<SerializedReservation[]> => {
    const items = await prisma.reservation.findMany({ where: { courseId }, select: { id: true, memberId: true, createdAt: true, updatedAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedReservation[]
  },

  getAllAsAdmin: async (page: number = 1, pageSize: number = 20): Promise<SerializedReservation[]> => {
    const items = await prisma.reservation.findMany({ select: { id: true, memberId: true, createdAt: true, updatedAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedReservation[]
  },

  getByIdAsAdmin: async (id: string): Promise<SerializedReservation> => {
    const item = await prisma.reservation.findFirst({ where: { id } })
    if (!item) notFound()
    return _serialize(item)
  },

  getById: async (courseId: string, id: string): Promise<SerializedReservation> => {
    const item = await prisma.reservation.findFirst({ where: { id, courseId } })
    if (!item) notFound()
    return _serialize(item)
  },

  create: async (courseId: string, data: CreateReservationInput): Promise<SerializedReservation> => {
    if (data.memberId) {
      const _owned_memberId = await prisma.member.findFirst({ where: { id: data.memberId, userId: courseId }, select: { id: true } })
      if (!_owned_memberId) throw new Error('Référence liée introuvable.')
    }
    const result = await prisma.reservation.create({
      data: { ...data, courseId }
    })
    return _serialize(result)
  },

  update: async (courseId: string, id: string, data: UpdateReservationInput): Promise<SerializedReservation> => {
    if (data.memberId) {
      const _owned_memberId = await prisma.member.findFirst({ where: { id: data.memberId, userId: courseId }, select: { id: true } })
      if (!_owned_memberId) throw new Error('Référence liée introuvable.')
    }
    const result = await prisma.reservation.update({
      where: { id, courseId },
      data: { ...data }
    })
    return _serialize(result)
  },

  delete: async (courseId: string, id: string): Promise<void> => {
    await prisma.reservation.delete({ where: { id, courseId } })
  },

  getByMemberId: async (userId: string, memberId: string, page: number = 1, pageSize: number = 20): Promise<SerializedReservation[]> => {
    const items = await prisma.reservation.findMany({ where: { memberId, courseId: userId }, select: { id: true, memberId: true, createdAt: true, updatedAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedReservation[]
  },

  getAllWithRelations: async (courseId: string, page: number = 1, pageSize: number = 20): Promise<SerializedReservation[]> => {
    const items = await prisma.reservation.findMany({ where: { courseId }, select: { id: true, memberId: true, createdAt: true, updatedAt: true, course: { select: { id: true, title: true, description: true, schedule: true } }, member: { select: { id: true } } }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString(), course: item.course ? { ...item.course, schedule: item.course.schedule.toISOString() } : item.course })) as SerializedReservation[]
  },

  getByIdWithRelations: async (courseId: string, id: string): Promise<SerializedReservation> => {
    const item = await prisma.reservation.findFirst({ where: { id, courseId }, select: { id: true, memberId: true, createdAt: true, updatedAt: true, course: { select: { id: true, title: true, description: true, schedule: true } }, member: { select: { id: true } } } })
    if (!item) notFound()
    return (item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString(), course: item.course ? { ...item.course, schedule: item.course.schedule.toISOString() } : item.course }))(item) as SerializedReservation
  },

  getByIdWithRelationsAsAdmin: async (id: string): Promise<SerializedReservation> => {
    const item = await prisma.reservation.findFirst({ where: { id }, select: { id: true, memberId: true, createdAt: true, updatedAt: true, course: { select: { id: true, title: true, description: true, schedule: true } }, member: { select: { id: true } } } })
    if (!item) notFound()
    return (item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString(), course: item.course ? { ...item.course, schedule: item.course.schedule.toISOString() } : item.course }))(item) as SerializedReservation
  },
}
