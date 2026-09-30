// AUTO-GÉNÉRÉ PAR dev_service_generator.py — NE PAS MODIFIER
import { notFound } from 'next/navigation'
import prisma from '@/lib/prisma'
import type { Subscription } from '@prisma/client'
import type { CreateSubscriptionInput, UpdateSubscriptionInput, SerializedSubscription } from '@/lib/types'

const _serialize = (item: Subscription): SerializedSubscription => {
  const { userId: _owner, ...rest } = item
  return ({
    ...rest,
  nextBillingDate: rest.nextBillingDate.toISOString(),
  createdAt: rest.createdAt.toISOString(),
  updatedAt: rest.updatedAt.toISOString(),
  monthlyPrice: Number(rest.monthlyPrice),
  }) as SerializedSubscription
}

export const subscriptionService = {
  getAll: async (userId: string, page: number = 1, pageSize: number = 20): Promise<SerializedSubscription[]> => {
    const items = await prisma.subscription.findMany({ where: { userId }, select: { id: true, name: true, monthlyPrice: true, nextBillingDate: true, status: true, categoryId: true, createdAt: true, updatedAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, nextBillingDate: item.nextBillingDate.toISOString(), createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString(), monthlyPrice: Number(item.monthlyPrice) })) as SerializedSubscription[]
  },

  getById: async (userId: string, id: string): Promise<SerializedSubscription> => {
    const item = await prisma.subscription.findFirst({ where: { id, userId } })
    if (!item) notFound()
    return _serialize(item)
  },

  create: async (userId: string, data: CreateSubscriptionInput): Promise<SerializedSubscription> => {
    if (data.categoryId) {
      const _owned_categoryId = await prisma.category.findFirst({ where: { id: data.categoryId, userId: userId }, select: { id: true } })
      if (!_owned_categoryId) throw new Error('Référence liée introuvable.')
    }
    const result = await prisma.subscription.create({
      data: { ...data, userId, status: 'active' }
    })
    return _serialize(result)
  },

  update: async (userId: string, id: string, data: UpdateSubscriptionInput): Promise<SerializedSubscription> => {
    if (data.categoryId) {
      const _owned_categoryId = await prisma.category.findFirst({ where: { id: data.categoryId, userId: userId }, select: { id: true } })
      if (!_owned_categoryId) throw new Error('Référence liée introuvable.')
    }
    if (data.status !== undefined) {
      const _cur = await prisma.subscription.findFirst({ where: { id, userId }, select: { status: true } })
      if (!_cur) notFound()
      if (data.status !== undefined && data.status !== _cur.status) {
        const _allowed: Record<string, string[]> = { active: ['paused', 'cancelled'], cancelled: [], paused: ['active', 'cancelled'] }
        if (!(_allowed[_cur.status] ?? []).includes(data.status)) {
          throw new Error(`Transition interdite : ${_cur.status} → ${data.status}`)
        }
      }
    }
    const result = await prisma.subscription.update({
      where: { id, userId },
      data: { ...data }
    })
    return _serialize(result)
  },

  delete: async (userId: string, id: string): Promise<void> => {
    await prisma.subscription.delete({ where: { id, userId } })
  },

  getByCategoryId: async (userId: string, categoryId: string, page: number = 1, pageSize: number = 20): Promise<SerializedSubscription[]> => {
    const items = await prisma.subscription.findMany({ where: { categoryId, userId: userId }, select: { id: true, name: true, monthlyPrice: true, nextBillingDate: true, status: true, categoryId: true, createdAt: true, updatedAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, nextBillingDate: item.nextBillingDate.toISOString(), createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString(), monthlyPrice: Number(item.monthlyPrice) })) as SerializedSubscription[]
  },

  getAllWithRelations: async (userId: string, page: number = 1, pageSize: number = 20): Promise<SerializedSubscription[]> => {
    const items = await prisma.subscription.findMany({ where: { userId }, select: { id: true, name: true, monthlyPrice: true, nextBillingDate: true, status: true, categoryId: true, createdAt: true, updatedAt: true, category: { select: { id: true, name: true, description: true } } }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, nextBillingDate: item.nextBillingDate.toISOString(), createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString(), monthlyPrice: Number(item.monthlyPrice) })) as SerializedSubscription[]
  },

  getByIdWithRelations: async (userId: string, id: string): Promise<SerializedSubscription> => {
    const item = await prisma.subscription.findFirst({ where: { id, userId }, select: { id: true, name: true, monthlyPrice: true, nextBillingDate: true, status: true, categoryId: true, createdAt: true, updatedAt: true, category: { select: { id: true, name: true, description: true } } } })
    if (!item) notFound()
    return (item => ({ ...item, nextBillingDate: item.nextBillingDate.toISOString(), createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString(), monthlyPrice: Number(item.monthlyPrice) }))(item) as SerializedSubscription
  },

  transitionTo: async (userId: string, id: string, newStatus: string, data: Partial<UpdateSubscriptionInput> = {}): Promise<SerializedSubscription> => {
    const _cur = await prisma.subscription.findFirst({ where: { id, userId }, select: { status: true } })
    if (!_cur) notFound()
    const _allowed: Record<string, string[]> = { active: ['paused', 'cancelled'], cancelled: [], paused: ['active', 'cancelled'] }
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
    const result = await prisma.subscription.update({ where: { id, userId }, data: { ..._payload, status: newStatus as Subscription['status'] } })
    return _serialize(result)
  },
}
