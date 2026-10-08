// AUTO-GÉNÉRÉ PAR dev_service_generator.py — NE PAS MODIFIER
import { notFound } from 'next/navigation'
import prisma from '@/lib/prisma'
import type { Action } from '@prisma/client'
import type { CreateActionInput, UpdateActionInput, SerializedAction } from '@/lib/types'

const _serialize = (item: Action): SerializedAction => {
  const { userId: _owner, ...rest } = item
  return ({
    ...rest,
  createdAt: rest.createdAt.toISOString(),
  updatedAt: rest.updatedAt.toISOString(),
  }) as SerializedAction
}

export const actionService = {
  getAll: async (userId: string, page: number = 1, pageSize: number = 20): Promise<SerializedAction[]> => {
    const items = await prisma.action.findMany({ where: { userId }, select: { id: true, description: true, status: true, interventionId: true, createdAt: true, updatedAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedAction[]
  },

  getById: async (userId: string, id: string): Promise<SerializedAction> => {
    const item = await prisma.action.findFirst({ where: { id, userId } })
    if (!item) notFound()
    return _serialize(item)
  },

  create: async (userId: string, data: CreateActionInput): Promise<SerializedAction> => {
    if (data.interventionId) {
      const _owned_interventionId = await prisma.intervention.findFirst({ where: { id: data.interventionId, userId: userId }, select: { id: true } })
      if (!_owned_interventionId) throw new Error('Référence liée introuvable.')
    }
    const result = await prisma.action.create({
      data: { ...data, userId, status: 'a_faire' }
    })
    return _serialize(result)
  },

  update: async (userId: string, id: string, data: UpdateActionInput): Promise<SerializedAction> => {
    if (data.interventionId) {
      const _owned_interventionId = await prisma.intervention.findFirst({ where: { id: data.interventionId, userId: userId }, select: { id: true } })
      if (!_owned_interventionId) throw new Error('Référence liée introuvable.')
    }
    if (data.status !== undefined) {
      const _cur = await prisma.action.findFirst({ where: { id, userId }, select: { status: true } })
      if (!_cur) notFound()
      if (data.status !== undefined && data.status !== _cur.status) {
        const _allowed: Record<string, string[]> = { a_faire: ['faite'], faite: [] }
        if (!(_allowed[_cur.status] ?? []).includes(data.status)) {
          throw new Error(`Transition interdite : ${_cur.status} → ${data.status}`)
        }
      }
    }
    const result = await prisma.action.update({
      where: { id, userId },
      data: { ...data }
    })
    return _serialize(result)
  },

  delete: async (userId: string, id: string): Promise<void> => {
    await prisma.action.delete({ where: { id, userId } })
  },

  getByInterventionId: async (userId: string, interventionId: string, page: number = 1, pageSize: number = 20): Promise<SerializedAction[]> => {
    const items = await prisma.action.findMany({ where: { interventionId, userId: userId }, select: { id: true, description: true, status: true, interventionId: true, createdAt: true, updatedAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedAction[]
  },

  getAllWithRelations: async (userId: string, page: number = 1, pageSize: number = 20): Promise<SerializedAction[]> => {
    const items = await prisma.action.findMany({ where: { userId }, select: { id: true, description: true, status: true, interventionId: true, createdAt: true, updatedAt: true, intervention: { select: { id: true, date: true, status: true } } }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString(), intervention: item.intervention ? { ...item.intervention, date: item.intervention.date.toISOString() } : item.intervention })) as SerializedAction[]
  },

  getByIdWithRelations: async (userId: string, id: string): Promise<SerializedAction> => {
    const item = await prisma.action.findFirst({ where: { id, userId }, select: { id: true, description: true, status: true, interventionId: true, createdAt: true, updatedAt: true, intervention: { select: { id: true, date: true, status: true } } } })
    if (!item) notFound()
    return (item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString(), intervention: item.intervention ? { ...item.intervention, date: item.intervention.date.toISOString() } : item.intervention }))(item) as SerializedAction
  },

  transitionTo: async (userId: string, id: string, newStatus: string, data: Partial<UpdateActionInput> = {}): Promise<SerializedAction> => {
    const _cur = await prisma.action.findFirst({ where: { id, userId }, select: { status: true } })
    if (!_cur) notFound()
    const _allowed: Record<string, string[]> = { a_faire: ['faite'], faite: [] }
    if (!(_allowed[_cur.status] ?? []).includes(newStatus)) {
      throw new Error(`Transition interdite : ${_cur.status} → ${newStatus}`)
    }
    // Seuls les champs déclarés pour l'état CIBLE sont écrits — jamais un champ
    // métier arbitraire (sinon transitionTo rouvrirait le verrou d'édition).
    const _fieldsByState: Record<string, string[]> = {}
    const _keep = new Set(_fieldsByState[newStatus] ?? [])
    const _payload: Partial<UpdateActionInput> = {}
    for (const _k of Object.keys(data)) {
      if (_keep.has(_k) && (data as Record<string, unknown>)[_k] !== undefined) {
        (_payload as Record<string, unknown>)[_k] = (data as Record<string, unknown>)[_k]
      }
    }
    const result = await prisma.action.update({ where: { id, userId }, data: { ..._payload, status: newStatus as Action['status'] } })
    return _serialize(result)
  },
}
