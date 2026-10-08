// AUTO-GÉNÉRÉ PAR dev_service_generator.py — NE PAS MODIFIER
import { notFound } from 'next/navigation'
import prisma from '@/lib/prisma'
import type { Subscription } from '@prisma/client'
import type { CreateSubscriptionInput, UpdateSubscriptionInput, SerializedSubscription } from '@/lib/types'

const _serialize = (item: Subscription): SerializedSubscription => {
  const { memberId: _owner, ...rest } = item
  return ({
    ...rest,
  renewalDate: rest.renewalDate.toISOString(),
  createdAt: rest.createdAt.toISOString(),
  updatedAt: rest.updatedAt.toISOString(),
  }) as SerializedSubscription
}

export const subscriptionService = {
  getAll: async (memberId: string, page: number = 1, pageSize: number = 20): Promise<SerializedSubscription[]> => {
    const items = await prisma.subscription.findMany({ where: { memberId }, select: { id: true, status: true, renewalDate: true, createdAt: true, updatedAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, renewalDate: item.renewalDate.toISOString(), createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedSubscription[]
  },

  getAllAsAdmin: async (page: number = 1, pageSize: number = 20): Promise<SerializedSubscription[]> => {
    const items = await prisma.subscription.findMany({ select: { id: true, status: true, renewalDate: true, createdAt: true, updatedAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, renewalDate: item.renewalDate.toISOString(), createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedSubscription[]
  },

  getByIdAsAdmin: async (id: string): Promise<SerializedSubscription> => {
    const item = await prisma.subscription.findFirst({ where: { id } })
    if (!item) notFound()
    return _serialize(item)
  },

  getById: async (memberId: string, id: string): Promise<SerializedSubscription> => {
    const item = await prisma.subscription.findFirst({ where: { id, memberId } })
    if (!item) notFound()
    return _serialize(item)
  },

  create: async (memberId: string, data: CreateSubscriptionInput): Promise<SerializedSubscription> => {
    const result = await prisma.subscription.create({
      data: { ...data, memberId, status: 'active' }
    })
    return _serialize(result)
  },

  update: async (memberId: string, id: string, data: UpdateSubscriptionInput): Promise<SerializedSubscription> => {
    const _cur = await prisma.subscription.findFirst({ where: { id, memberId }, select: { status: true } })
    if (!_cur) notFound()
    if ((['cancelled'] as string[]).includes(_cur.status)) {
      const _touched = Object.keys(data).filter(_k => _k !== 'status' && (data as Record<string, unknown>)[_k] !== undefined)
      if (_touched.length > 0) {
        throw new Error(`Cette fiche n'est plus modifiable dans son état actuel.`)
      }
    }
    if (data.status !== undefined && data.status !== _cur.status) {
      const _allowed: Record<string, string[]> = { active: ['inactive', 'cancelled'], cancelled: [], inactive: ['active'] }
      if (!(_allowed[_cur.status] ?? []).includes(data.status)) {
        throw new Error(`Transition interdite : ${_cur.status} → ${data.status}`)
      }
    }
    const result = await prisma.subscription.update({
      where: { id, memberId },
      data: { ...data }
    })
    return _serialize(result)
  },

  delete: async (memberId: string, id: string): Promise<void> => {
    await prisma.subscription.delete({ where: { id, memberId } })
  },

  getAllWithRelations: async (memberId: string, page: number = 1, pageSize: number = 20): Promise<SerializedSubscription[]> => {
    const items = await prisma.subscription.findMany({ where: { memberId }, select: { id: true, status: true, renewalDate: true, createdAt: true, updatedAt: true, member: { select: { id: true } } }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, renewalDate: item.renewalDate.toISOString(), createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedSubscription[]
  },

  getByIdWithRelations: async (memberId: string, id: string): Promise<SerializedSubscription> => {
    const item = await prisma.subscription.findFirst({ where: { id, memberId }, select: { id: true, status: true, renewalDate: true, createdAt: true, updatedAt: true, member: { select: { id: true } } } })
    if (!item) notFound()
    return (item => ({ ...item, renewalDate: item.renewalDate.toISOString(), createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() }))(item) as SerializedSubscription
  },

  getByIdWithRelationsAsAdmin: async (id: string): Promise<SerializedSubscription> => {
    const item = await prisma.subscription.findFirst({ where: { id }, select: { id: true, status: true, renewalDate: true, createdAt: true, updatedAt: true, member: { select: { id: true } } } })
    if (!item) notFound()
    return (item => ({ ...item, renewalDate: item.renewalDate.toISOString(), createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() }))(item) as SerializedSubscription
  },

  transitionTo: async (memberId: string, id: string, newStatus: string, data: Partial<UpdateSubscriptionInput> = {}): Promise<SerializedSubscription> => {
    const _cur = await prisma.subscription.findFirst({ where: { id }, select: { status: true } })
    if (!_cur) notFound()
    const _allowed: Record<string, string[]> = { active: ['inactive', 'cancelled'], cancelled: [], inactive: ['active'] }
    if (!(_allowed[_cur.status] ?? []).includes(newStatus)) {
      throw new Error(`Transition interdite : ${_cur.status} → ${newStatus}`)
    }
    // Seuls les champs déclarés pour l'état CIBLE sont écrits — jamais un champ
    // métier arbitraire (sinon transitionTo rouvrirait le verrou d'édition).
    const _fieldsByState: Record<string, string[]> = {}
    const _keep = new Set(_fieldsByState[newStatus] ?? [])
    const _payload: Partial<UpdateSubscriptionInput> = {}
    for (const _k of Object.keys(data)) {
      if (_keep.has(_k) && (data as Record<string, unknown>)[_k] !== undefined) {
        (_payload as Record<string, unknown>)[_k] = (data as Record<string, unknown>)[_k]
      }
    }
    const result = await prisma.subscription.update({ where: { id }, data: { ..._payload, status: newStatus as Subscription['status'] } })
    return _serialize(result)
  },
}
