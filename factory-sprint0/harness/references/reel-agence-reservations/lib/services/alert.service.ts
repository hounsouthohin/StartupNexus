// AUTO-GÉNÉRÉ PAR dev_service_generator.py — NE PAS MODIFIER
import { notFound } from 'next/navigation'
import prisma from '@/lib/prisma'
import type { Alert } from '@prisma/client'
import type { CreateAlertInput, UpdateAlertInput, SerializedAlert } from '@/lib/types'

const _serialize = (item: Alert): SerializedAlert => {
  const { userId: _owner, ...rest } = item
  return ({
    ...rest,
  createdAt: rest.createdAt.toISOString(),
  updatedAt: rest.updatedAt.toISOString(),
  }) as SerializedAlert
}

export const alertService = {
  getAll: async (userId: string, page: number = 1, pageSize: number = 20): Promise<SerializedAlert[]> => {
    const items = await prisma.alert.findMany({ where: { userId }, select: { id: true, message: true, reservationId: true, createdAt: true, updatedAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedAlert[]
  },

  getById: async (userId: string, id: string): Promise<SerializedAlert> => {
    const item = await prisma.alert.findFirst({ where: { id, userId } })
    if (!item) notFound()
    return _serialize(item)
  },

  create: async (userId: string, data: CreateAlertInput): Promise<SerializedAlert> => {
    if (data.reservationId) {
      const _owned_reservationId = await prisma.reservation.findFirst({ where: { id: data.reservationId, clientId: userId }, select: { id: true } })
      if (!_owned_reservationId) throw new Error('Référence liée introuvable.')
    }
    const result = await prisma.alert.create({
      data: { ...data, userId }
    })
    return _serialize(result)
  },

  update: async (userId: string, id: string, data: UpdateAlertInput): Promise<SerializedAlert> => {
    if (data.reservationId) {
      const _owned_reservationId = await prisma.reservation.findFirst({ where: { id: data.reservationId, clientId: userId }, select: { id: true } })
      if (!_owned_reservationId) throw new Error('Référence liée introuvable.')
    }
    const result = await prisma.alert.update({
      where: { id, userId },
      data: { ...data }
    })
    return _serialize(result)
  },

  delete: async (userId: string, id: string): Promise<void> => {
    await prisma.alert.delete({ where: { id, userId } })
  },

  getByReservationId: async (userId: string, reservationId: string, page: number = 1, pageSize: number = 20): Promise<SerializedAlert[]> => {
    const items = await prisma.alert.findMany({ where: { reservationId, userId: userId }, select: { id: true, message: true, reservationId: true, createdAt: true, updatedAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedAlert[]
  },

  getAllWithRelations: async (userId: string, page: number = 1, pageSize: number = 20): Promise<SerializedAlert[]> => {
    const items = await prisma.alert.findMany({ where: { userId }, select: { id: true, message: true, reservationId: true, createdAt: true, updatedAt: true, reservation: { select: { id: true, date: true, status: true } } }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString(), reservation: item.reservation ? { ...item.reservation, date: item.reservation.date.toISOString() } : item.reservation })) as SerializedAlert[]
  },

  getByIdWithRelations: async (userId: string, id: string): Promise<SerializedAlert> => {
    const item = await prisma.alert.findFirst({ where: { id, userId }, select: { id: true, message: true, reservationId: true, createdAt: true, updatedAt: true, reservation: { select: { id: true, date: true, status: true } } } })
    if (!item) notFound()
    return (item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString(), reservation: item.reservation ? { ...item.reservation, date: item.reservation.date.toISOString() } : item.reservation }))(item) as SerializedAlert
  },
}
