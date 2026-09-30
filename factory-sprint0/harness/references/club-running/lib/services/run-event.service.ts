// AUTO-GÉNÉRÉ PAR dev_service_generator.py — NE PAS MODIFIER
import { notFound } from 'next/navigation'
import prisma from '@/lib/prisma'
import type { RunEvent } from '@prisma/client'
import type { CreateRunEventInput, UpdateRunEventInput, SerializedRunEvent } from '@/lib/types'

const _serialize = (item: RunEvent): SerializedRunEvent => {
  const { userId: _owner, ...rest } = item
  return ({
    ...rest,
  dateTime: rest.dateTime.toISOString(),
  createdAt: rest.createdAt.toISOString(),
  updatedAt: rest.updatedAt.toISOString(),
  }) as SerializedRunEvent
}

export const runEventService = {
  getAll: async (userId: string, page: number = 1, pageSize: number = 20): Promise<SerializedRunEvent[]> => {
    const items = await prisma.runEvent.findMany({ where: { userId }, select: { id: true, title: true, dateTime: true, location: true, distance: true, description: true, status: true, createdAt: true, updatedAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, dateTime: item.dateTime.toISOString(), createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedRunEvent[]
  },

  getById: async (userId: string, id: string): Promise<SerializedRunEvent> => {
    const item = await prisma.runEvent.findFirst({ where: { id, userId } })
    if (!item) notFound()
    return _serialize(item)
  },

  create: async (userId: string, data: CreateRunEventInput): Promise<SerializedRunEvent> => {
    const result = await prisma.runEvent.create({
      data: { ...data, userId, status: 'ouverte' }
    })
    return _serialize(result)
  },

  update: async (userId: string, id: string, data: UpdateRunEventInput): Promise<SerializedRunEvent> => {
    if (data.status !== undefined) {
      const _cur = await prisma.runEvent.findFirst({ where: { id, userId }, select: { status: true } })
      if (!_cur) notFound()
      if (data.status !== undefined && data.status !== _cur.status) {
        const _allowed: Record<string, string[]> = { annulee: [], complete: [], ouverte: ['complete', 'annulee'] }
        if (!(_allowed[_cur.status] ?? []).includes(data.status)) {
          throw new Error(`Transition interdite : ${_cur.status} → ${data.status}`)
        }
      }
    }
    const result = await prisma.runEvent.update({
      where: { id, userId },
      data: { ...data }
    })
    return _serialize(result)
  },

  delete: async (userId: string, id: string): Promise<void> => {
    await prisma.runEvent.delete({ where: { id, userId } })
  },

  getPublicById: async (id: string): Promise<SerializedRunEvent> => {
    const item = await prisma.runEvent.findUnique({ where: { id } })
    if (!item) notFound()
    return _serialize(item)
  },

  getPublicAll: async (page: number = 1, pageSize: number = 20): Promise<SerializedRunEvent[]> => {
    const items = await prisma.runEvent.findMany({ where: { status: 'ouverte' }, select: { id: true, title: true, dateTime: true, location: true, distance: true, description: true, status: true, createdAt: true, updatedAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, dateTime: item.dateTime.toISOString(), createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedRunEvent[]
  },

  getAllWithRelations: async (userId: string, page: number = 1, pageSize: number = 20): Promise<SerializedRunEvent[]> => {
    const items = await prisma.runEvent.findMany({ where: { userId }, select: { id: true, title: true, dateTime: true, location: true, distance: true, description: true, status: true, createdAt: true, updatedAt: true, participants: { select: { id: true, name: true, email: true } } }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, dateTime: item.dateTime.toISOString(), createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedRunEvent[]
  },

  getByIdWithRelations: async (userId: string, id: string): Promise<SerializedRunEvent> => {
    const item = await prisma.runEvent.findFirst({ where: { id, userId }, select: { id: true, title: true, dateTime: true, location: true, distance: true, description: true, status: true, createdAt: true, updatedAt: true, participants: { select: { id: true, name: true, email: true } } } })
    if (!item) notFound()
    return (item => ({ ...item, dateTime: item.dateTime.toISOString(), createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() }))(item) as SerializedRunEvent
  },

  getPublicByIdWithRelations: async (id: string): Promise<SerializedRunEvent> => {
    const item = await prisma.runEvent.findUnique({ where: { id }, select: { id: true, title: true, dateTime: true, location: true, distance: true, description: true, status: true, createdAt: true, updatedAt: true, participants: { select: { id: true, name: true, email: true } } } })
    if (!item) notFound()
    return (item => ({ ...item, dateTime: item.dateTime.toISOString(), createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() }))(item) as SerializedRunEvent
  },

  transitionTo: async (userId: string, id: string, newStatus: string, data: Partial<UpdateRunEventInput> = {}): Promise<SerializedRunEvent> => {
    const _cur = await prisma.runEvent.findFirst({ where: { id, userId }, select: { status: true } })
    if (!_cur) notFound()
    const _allowed: Record<string, string[]> = { annulee: [], complete: [], ouverte: ['complete', 'annulee'] }
    if (!(_allowed[_cur.status] ?? []).includes(newStatus)) {
      throw new Error(`Transition interdite : ${_cur.status} → ${newStatus}`)
    }
    // Seuls les champs déclarés pour l'état CIBLE sont écrits — jamais un champ
    // métier arbitraire (sinon transitionTo rouvrirait le verrou d'édition).
    const _fieldsByState: Record<string, string[]> = {}
    const _keep = new Set(_fieldsByState[newStatus] ?? [])
    const _payload: Partial<UpdateRunEventInput> = {}
    for (const _k of Object.keys(data)) {
      if (_keep.has(_k) && (data as Record<string, unknown>)[_k] !== undefined) {
        (_payload as Record<string, unknown>)[_k] = (data as Record<string, unknown>)[_k]
      }
    }
    const result = await prisma.runEvent.update({ where: { id, userId }, data: { ..._payload, status: newStatus as RunEvent['status'] } })
    return _serialize(result)
  },
}
