// AUTO-GÉNÉRÉ PAR dev_service_generator.py — NE PAS MODIFIER
import { notFound } from 'next/navigation'
import prisma from '@/lib/prisma'
import type { Payment } from '@prisma/client'
import type { CreatePaymentInput, UpdatePaymentInput, SerializedPayment } from '@/lib/types'

const _serialize = (item: Payment): SerializedPayment => {
  const { subscriptionId: _owner, ...rest } = item
  return ({
    ...rest,
  date: rest.date.toISOString(),
  createdAt: rest.createdAt.toISOString(),
  updatedAt: rest.updatedAt.toISOString(),
  }) as SerializedPayment
}

export const paymentService = {
  getAll: async (subscriptionId: string, page: number = 1, pageSize: number = 20): Promise<SerializedPayment[]> => {
    const items = await prisma.payment.findMany({ where: { subscriptionId }, select: { id: true, amount: true, date: true, createdAt: true, updatedAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, date: item.date.toISOString(), createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedPayment[]
  },

  getAllAsAdmin: async (page: number = 1, pageSize: number = 20): Promise<SerializedPayment[]> => {
    const items = await prisma.payment.findMany({ select: { id: true, amount: true, date: true, createdAt: true, updatedAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, date: item.date.toISOString(), createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedPayment[]
  },

  getByIdAsAdmin: async (id: string): Promise<SerializedPayment> => {
    const item = await prisma.payment.findFirst({ where: { id } })
    if (!item) notFound()
    return _serialize(item)
  },

  getById: async (subscriptionId: string, id: string): Promise<SerializedPayment> => {
    const item = await prisma.payment.findFirst({ where: { id, subscriptionId } })
    if (!item) notFound()
    return _serialize(item)
  },

  create: async (subscriptionId: string, data: CreatePaymentInput): Promise<SerializedPayment> => {
    const result = await prisma.payment.create({
      data: { ...data, subscriptionId }
    })
    return _serialize(result)
  },

  update: async (subscriptionId: string, id: string, data: UpdatePaymentInput): Promise<SerializedPayment> => {
    const result = await prisma.payment.update({
      where: { id, subscriptionId },
      data: { ...data }
    })
    return _serialize(result)
  },

  delete: async (subscriptionId: string, id: string): Promise<void> => {
    await prisma.payment.delete({ where: { id, subscriptionId } })
  },

  getAllWithRelations: async (subscriptionId: string, page: number = 1, pageSize: number = 20): Promise<SerializedPayment[]> => {
    const items = await prisma.payment.findMany({ where: { subscriptionId }, select: { id: true, amount: true, date: true, createdAt: true, updatedAt: true, subscription: { select: { id: true, status: true, renewalDate: true } } }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, date: item.date.toISOString(), createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString(), subscription: item.subscription ? { ...item.subscription, renewalDate: item.subscription.renewalDate.toISOString() } : item.subscription })) as SerializedPayment[]
  },

  getByIdWithRelations: async (subscriptionId: string, id: string): Promise<SerializedPayment> => {
    const item = await prisma.payment.findFirst({ where: { id, subscriptionId }, select: { id: true, amount: true, date: true, createdAt: true, updatedAt: true, subscription: { select: { id: true, status: true, renewalDate: true } } } })
    if (!item) notFound()
    return (item => ({ ...item, date: item.date.toISOString(), createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString(), subscription: item.subscription ? { ...item.subscription, renewalDate: item.subscription.renewalDate.toISOString() } : item.subscription }))(item) as SerializedPayment
  },

  getByIdWithRelationsAsAdmin: async (id: string): Promise<SerializedPayment> => {
    const item = await prisma.payment.findFirst({ where: { id }, select: { id: true, amount: true, date: true, createdAt: true, updatedAt: true, subscription: { select: { id: true, status: true, renewalDate: true } } } })
    if (!item) notFound()
    return (item => ({ ...item, date: item.date.toISOString(), createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString(), subscription: item.subscription ? { ...item.subscription, renewalDate: item.subscription.renewalDate.toISOString() } : item.subscription }))(item) as SerializedPayment
  },
}
