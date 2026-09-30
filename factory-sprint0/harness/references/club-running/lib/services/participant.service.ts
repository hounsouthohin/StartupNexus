// AUTO-GÉNÉRÉ PAR dev_service_generator.py — NE PAS MODIFIER
import { notFound } from 'next/navigation'
import prisma from '@/lib/prisma'
import type { Participant } from '@prisma/client'
import type { CreateParticipantInput, UpdateParticipantInput, SerializedParticipant } from '@/lib/types'

const _serialize = (item: Participant): SerializedParticipant => {
  const { userId: _owner, ...rest } = item
  return ({
    ...rest,
  createdAt: rest.createdAt.toISOString(),
  updatedAt: rest.updatedAt.toISOString(),
  }) as SerializedParticipant
}

export const participantService = {
  getAll: async (userId: string, page: number = 1, pageSize: number = 20): Promise<SerializedParticipant[]> => {
    const items = await prisma.participant.findMany({ where: { userId }, select: { id: true, name: true, email: true, runEventId: true, createdAt: true, updatedAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedParticipant[]
  },

  getById: async (userId: string, id: string): Promise<SerializedParticipant> => {
    const item = await prisma.participant.findFirst({ where: { id, userId } })
    if (!item) notFound()
    return _serialize(item)
  },

  create: async (userId: string, data: CreateParticipantInput): Promise<SerializedParticipant> => {
    if (data.runEventId) {
      const _owned_runEventId = await prisma.runEvent.findFirst({ where: { id: data.runEventId, userId: userId }, select: { id: true } })
      if (!_owned_runEventId) throw new Error('Référence liée introuvable.')
    }
    const result = await prisma.participant.create({
      data: { ...data, userId }
    })
    return _serialize(result)
  },

  update: async (userId: string, id: string, data: UpdateParticipantInput): Promise<SerializedParticipant> => {
    if (data.runEventId) {
      const _owned_runEventId = await prisma.runEvent.findFirst({ where: { id: data.runEventId, userId: userId }, select: { id: true } })
      if (!_owned_runEventId) throw new Error('Référence liée introuvable.')
    }
    const result = await prisma.participant.update({
      where: { id, userId },
      data: { ...data }
    })
    return _serialize(result)
  },

  delete: async (userId: string, id: string): Promise<void> => {
    await prisma.participant.delete({ where: { id, userId } })
  },

  getByRunEventId: async (userId: string, runEventId: string, page: number = 1, pageSize: number = 20): Promise<SerializedParticipant[]> => {
    const items = await prisma.participant.findMany({ where: { runEventId, userId: userId }, select: { id: true, name: true, email: true, runEventId: true, createdAt: true, updatedAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedParticipant[]
  },

  getAllWithRelations: async (userId: string, page: number = 1, pageSize: number = 20): Promise<SerializedParticipant[]> => {
    const items = await prisma.participant.findMany({ where: { userId }, select: { id: true, name: true, email: true, runEventId: true, createdAt: true, updatedAt: true, runEvent: { select: { id: true, title: true, dateTime: true, location: true, distance: true } } }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString(), runEvent: item.runEvent ? { ...item.runEvent, dateTime: item.runEvent.dateTime.toISOString() } : item.runEvent })) as SerializedParticipant[]
  },

  getByIdWithRelations: async (userId: string, id: string): Promise<SerializedParticipant> => {
    const item = await prisma.participant.findFirst({ where: { id, userId }, select: { id: true, name: true, email: true, runEventId: true, createdAt: true, updatedAt: true, runEvent: { select: { id: true, title: true, dateTime: true, location: true, distance: true } } } })
    if (!item) notFound()
    return (item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString(), runEvent: item.runEvent ? { ...item.runEvent, dateTime: item.runEvent.dateTime.toISOString() } : item.runEvent }))(item) as SerializedParticipant
  },
}
