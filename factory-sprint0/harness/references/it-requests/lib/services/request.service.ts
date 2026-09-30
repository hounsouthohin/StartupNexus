// AUTO-GÉNÉRÉ PAR dev_service_generator.py — NE PAS MODIFIER
import { notFound } from 'next/navigation'
import prisma from '@/lib/prisma'
import type { Request } from '@prisma/client'
import type { CreateRequestInput, UpdateRequestInput, SerializedRequest } from '@/lib/types'

const _serialize = (item: Request): SerializedRequest => {
  const { userId: _owner, ...rest } = item
  return ({
    ...rest,
  createdAt: rest.createdAt.toISOString(),
  updatedAt: rest.updatedAt.toISOString(),
  }) as SerializedRequest
}

export const requestService = {
  getAll: async (userId: string, page: number = 1, pageSize: number = 20): Promise<SerializedRequest[]> => {
    const items = await prisma.request.findMany({ where: { userId }, select: { id: true, title: true, description: true, priority: true, status: true, createdAt: true, updatedAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedRequest[]
  },

  getAllAsAdmin: async (page: number = 1, pageSize: number = 20): Promise<SerializedRequest[]> => {
    const items = await prisma.request.findMany({ select: { id: true, title: true, description: true, priority: true, status: true, createdAt: true, updatedAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedRequest[]
  },

  getByIdAsAdmin: async (id: string): Promise<SerializedRequest> => {
    const item = await prisma.request.findFirst({ where: { id } })
    if (!item) notFound()
    return _serialize(item)
  },

  getById: async (userId: string, id: string): Promise<SerializedRequest> => {
    const item = await prisma.request.findFirst({ where: { id, userId } })
    if (!item) notFound()
    return _serialize(item)
  },

  create: async (userId: string, data: CreateRequestInput): Promise<SerializedRequest> => {
    const result = await prisma.request.create({
      data: { ...data, userId, status: 'new' }
    })
    return _serialize(result)
  },

  update: async (userId: string, id: string, data: UpdateRequestInput): Promise<SerializedRequest> => {
    if (data.status !== undefined) {
      const _cur = await prisma.request.findFirst({ where: { id, userId }, select: { status: true } })
      if (!_cur) notFound()
      if (data.status !== undefined && data.status !== _cur.status) {
        const _allowed: Record<string, string[]> = { in_progress: ['resolved'], new: ['in_progress'], resolved: [] }
        if (!(_allowed[_cur.status] ?? []).includes(data.status)) {
          throw new Error(`Transition interdite : ${_cur.status} → ${data.status}`)
        }
      }
    }
    const result = await prisma.request.update({
      where: { id, userId },
      data: { ...data }
    })
    return _serialize(result)
  },

  delete: async (userId: string, id: string): Promise<void> => {
    await prisma.request.delete({ where: { id, userId } })
  },

  transitionTo: async (userId: string, id: string, newStatus: string, data: Partial<UpdateRequestInput> = {}): Promise<SerializedRequest> => {
    const _cur = await prisma.request.findFirst({ where: { id }, select: { status: true } })
    if (!_cur) notFound()
    const _allowed: Record<string, string[]> = { in_progress: ['resolved'], new: ['in_progress'], resolved: [] }
    if (!(_allowed[_cur.status] ?? []).includes(newStatus)) {
      throw new Error(`Transition interdite : ${_cur.status} → ${newStatus}`)
    }
    // Seuls les champs déclarés pour l'état CIBLE sont écrits — jamais un champ
    // métier arbitraire (sinon transitionTo rouvrirait le verrou d'édition).
    const _fieldsByState: Record<string, string[]> = {}
    const _keep = new Set(_fieldsByState[newStatus] ?? [])
    const _payload: Partial<UpdateRequestInput> = {}
    for (const _k of Object.keys(data)) {
      if (_keep.has(_k) && (data as Record<string, unknown>)[_k] !== undefined) {
        (_payload as Record<string, unknown>)[_k] = (data as Record<string, unknown>)[_k]
      }
    }
    const result = await prisma.request.update({ where: { id }, data: { ..._payload, status: newStatus as Request['status'] } })
    return _serialize(result)
  },
}
