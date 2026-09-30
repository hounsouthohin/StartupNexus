// AUTO-GÉNÉRÉ PAR dev_service_generator.py — NE PAS MODIFIER
import { notFound } from 'next/navigation'
import prisma from '@/lib/prisma'
import type { Slot } from '@prisma/client'
import type { CreateSlotInput, UpdateSlotInput, SerializedSlot } from '@/lib/types'

const _serialize = (item: Slot): SerializedSlot => {
  const { workshopId: _owner, ...rest } = item
  return ({
    ...rest,
  startTime: rest.startTime.toISOString(),
  endTime: rest.endTime.toISOString(),
  createdAt: rest.createdAt.toISOString(),
  updatedAt: rest.updatedAt.toISOString(),
  }) as SerializedSlot
}

export const slotService = {
  getAll: async (workshopId: string, page: number = 1, pageSize: number = 20): Promise<SerializedSlot[]> => {
    const items = await prisma.slot.findMany({ where: { workshopId }, select: { id: true, startTime: true, endTime: true, createdAt: true, updatedAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, startTime: item.startTime.toISOString(), endTime: item.endTime.toISOString(), createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedSlot[]
  },

  getById: async (workshopId: string, id: string): Promise<SerializedSlot> => {
    const item = await prisma.slot.findFirst({ where: { id, workshopId } })
    if (!item) notFound()
    return _serialize(item)
  },

  create: async (workshopId: string, data: CreateSlotInput): Promise<SerializedSlot> => {
    const result = await prisma.slot.create({
      data: { ...data, workshopId }
    })
    return _serialize(result)
  },

  update: async (workshopId: string, id: string, data: UpdateSlotInput): Promise<SerializedSlot> => {
    const result = await prisma.slot.update({
      where: { id, workshopId },
      data: { ...data }
    })
    return _serialize(result)
  },

  delete: async (workshopId: string, id: string): Promise<void> => {
    await prisma.slot.delete({ where: { id, workshopId } })
  },

  getAllWithRelations: async (workshopId: string, page: number = 1, pageSize: number = 20): Promise<SerializedSlot[]> => {
    const items = await prisma.slot.findMany({ where: { workshopId }, select: { id: true, startTime: true, endTime: true, createdAt: true, updatedAt: true, workshop: { select: { id: true, title: true, description: true, duration: true, price: true } }, reservations: { select: { id: true, status: true, reason: true } } }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, startTime: item.startTime.toISOString(), endTime: item.endTime.toISOString(), createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedSlot[]
  },

  getByIdWithRelations: async (workshopId: string, id: string): Promise<SerializedSlot> => {
    const item = await prisma.slot.findFirst({ where: { id, workshopId }, select: { id: true, startTime: true, endTime: true, createdAt: true, updatedAt: true, workshop: { select: { id: true, title: true, description: true, duration: true, price: true } }, reservations: { select: { id: true, status: true, reason: true } } } })
    if (!item) notFound()
    return (item => ({ ...item, startTime: item.startTime.toISOString(), endTime: item.endTime.toISOString(), createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() }))(item) as SerializedSlot
  },
}
