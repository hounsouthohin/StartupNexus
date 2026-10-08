// AUTO-GÉNÉRÉ PAR dev_service_generator.py — NE PAS MODIFIER
import { notFound } from 'next/navigation'
import prisma from '@/lib/prisma'
import type { Member } from '@prisma/client'
import type { CreateMemberInput, UpdateMemberInput, SerializedMember } from '@/lib/types'

const _serialize = (item: Member): SerializedMember => {
  const { userId: _owner, ...rest } = item
  return ({
    ...rest,
  createdAt: rest.createdAt.toISOString(),
  updatedAt: rest.updatedAt.toISOString(),
  }) as SerializedMember
}

export const memberService = {
  getAll: async (userId: string, page: number = 1, pageSize: number = 20): Promise<SerializedMember[]> => {
    const items = await prisma.member.findMany({ where: { userId }, select: { id: true, subscriptionId: true, createdAt: true, updatedAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedMember[]
  },

  getAllAsAdmin: async (page: number = 1, pageSize: number = 20): Promise<SerializedMember[]> => {
    const items = await prisma.member.findMany({ select: { id: true, subscriptionId: true, createdAt: true, updatedAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedMember[]
  },

  getByIdAsAdmin: async (id: string): Promise<SerializedMember> => {
    const item = await prisma.member.findFirst({ where: { id } })
    if (!item) notFound()
    return _serialize(item)
  },

  getById: async (userId: string, id: string): Promise<SerializedMember> => {
    const item = await prisma.member.findFirst({ where: { id, userId } })
    if (!item) notFound()
    return _serialize(item)
  },

  create: async (userId: string, data: CreateMemberInput): Promise<SerializedMember> => {
    if (data.subscriptionId) {
      const _owned_subscriptionId = await prisma.subscription.findFirst({ where: { id: data.subscriptionId, memberId: userId }, select: { id: true } })
      if (!_owned_subscriptionId) throw new Error('Référence liée introuvable.')
    }
    const result = await prisma.member.create({
      data: { ...data, userId }
    })
    return _serialize(result)
  },

  update: async (userId: string, id: string, data: UpdateMemberInput): Promise<SerializedMember> => {
    if (data.subscriptionId) {
      const _owned_subscriptionId = await prisma.subscription.findFirst({ where: { id: data.subscriptionId, memberId: userId }, select: { id: true } })
      if (!_owned_subscriptionId) throw new Error('Référence liée introuvable.')
    }
    const result = await prisma.member.update({
      where: { id, userId },
      data: { ...data }
    })
    return _serialize(result)
  },

  delete: async (userId: string, id: string): Promise<void> => {
    await prisma.member.delete({ where: { id, userId } })
  },

  getBySubscriptionId: async (userId: string, subscriptionId: string, page: number = 1, pageSize: number = 20): Promise<SerializedMember[]> => {
    const items = await prisma.member.findMany({ where: { subscriptionId, userId: userId }, select: { id: true, subscriptionId: true, createdAt: true, updatedAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedMember[]
  },
}
