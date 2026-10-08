// AUTO-GÉNÉRÉ PAR dev_service_generator.py — NE PAS MODIFIER
import { notFound } from 'next/navigation'
import prisma from '@/lib/prisma'
import type { RoomReservation } from '@prisma/client'
import type { CreateRoomReservationInput, UpdateRoomReservationInput, SerializedRoomReservation } from '@/lib/types'

const _serialize = (item: RoomReservation): SerializedRoomReservation => {
  const { userId: _owner, ...rest } = item
  return ({
    ...rest,
  date: rest.date.toISOString(),
  createdAt: rest.createdAt.toISOString(),
  updatedAt: rest.updatedAt.toISOString(),
  }) as SerializedRoomReservation
}

export const roomReservationService = {
  getAll: async (userId: string, page: number = 1, pageSize: number = 20): Promise<SerializedRoomReservation[]> => {
    const items = await prisma.roomReservation.findMany({ where: { userId }, select: { id: true, roomId: true, date: true, createdAt: true, updatedAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, date: item.date.toISOString(), createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedRoomReservation[]
  },

  getAllAsAdmin: async (page: number = 1, pageSize: number = 20): Promise<SerializedRoomReservation[]> => {
    const items = await prisma.roomReservation.findMany({ select: { id: true, roomId: true, date: true, createdAt: true, updatedAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, date: item.date.toISOString(), createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedRoomReservation[]
  },

  getByIdAsAdmin: async (id: string): Promise<SerializedRoomReservation> => {
    const item = await prisma.roomReservation.findFirst({ where: { id } })
    if (!item) notFound()
    return _serialize(item)
  },

  getById: async (userId: string, id: string): Promise<SerializedRoomReservation> => {
    const item = await prisma.roomReservation.findFirst({ where: { id, userId } })
    if (!item) notFound()
    return _serialize(item)
  },

  create: async (userId: string, data: CreateRoomReservationInput): Promise<SerializedRoomReservation> => {
    const result = await prisma.roomReservation.create({
      data: { ...data, userId }
    })
    return _serialize(result)
  },

  update: async (userId: string, id: string, data: UpdateRoomReservationInput): Promise<SerializedRoomReservation> => {
    const result = await prisma.roomReservation.update({
      where: { id, userId },
      data: { ...data }
    })
    return _serialize(result)
  },

  delete: async (userId: string, id: string): Promise<void> => {
    await prisma.roomReservation.delete({ where: { id, userId } })
  },

  getAllWithRelations: async (userId: string, page: number = 1, pageSize: number = 20): Promise<SerializedRoomReservation[]> => {
    const items = await prisma.roomReservation.findMany({ where: { userId }, select: { id: true, roomId: true, date: true, createdAt: true, updatedAt: true, room: { select: { id: true } } }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, date: item.date.toISOString(), createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedRoomReservation[]
  },

  getByIdWithRelations: async (userId: string, id: string): Promise<SerializedRoomReservation> => {
    const item = await prisma.roomReservation.findFirst({ where: { id, userId }, select: { id: true, roomId: true, date: true, createdAt: true, updatedAt: true, room: { select: { id: true } } } })
    if (!item) notFound()
    return (item => ({ ...item, date: item.date.toISOString(), createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() }))(item) as SerializedRoomReservation
  },

  getByIdWithRelationsAsAdmin: async (id: string): Promise<SerializedRoomReservation> => {
    const item = await prisma.roomReservation.findFirst({ where: { id }, select: { id: true, roomId: true, date: true, createdAt: true, updatedAt: true, room: { select: { id: true } } } })
    if (!item) notFound()
    return (item => ({ ...item, date: item.date.toISOString(), createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() }))(item) as SerializedRoomReservation
  },
}
