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
    const items = await prisma.member.findMany({ where: { userId }, select: { id: true, name: true, email: true, phone: true, createdAt: true, updatedAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedMember[]
  },

  getById: async (userId: string, id: string): Promise<SerializedMember> => {
    const item = await prisma.member.findFirst({ where: { id, userId } })
    if (!item) notFound()
    return _serialize(item)
  },

  create: async (userId: string, data: CreateMemberInput): Promise<SerializedMember> => {
    const result = await prisma.member.create({
      data: { ...data, userId }
    })
    return _serialize(result)
  },

  update: async (userId: string, id: string, data: UpdateMemberInput): Promise<SerializedMember> => {
    const result = await prisma.member.update({
      where: { id, userId },
      data: { ...data }
    })
    return _serialize(result)
  },

  delete: async (userId: string, id: string): Promise<void> => {
    await prisma.member.delete({ where: { id, userId } })
  },

  getAllWithRelations: async (userId: string, page: number = 1, pageSize: number = 20): Promise<SerializedMember[]> => {
    const items = await prisma.member.findMany({ where: { userId }, select: { id: true, name: true, email: true, phone: true, createdAt: true, updatedAt: true, borrowings: { select: { id: true, requestDate: true, status: true } } }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString(), borrowings: (item.borrowings ?? []).map(c => ({ ...c, requestDate: c.requestDate.toISOString() })) })) as SerializedMember[]
  },

  getByIdWithRelations: async (userId: string, id: string): Promise<SerializedMember> => {
    const item = await prisma.member.findFirst({ where: { id, userId }, select: { id: true, name: true, email: true, phone: true, createdAt: true, updatedAt: true, borrowings: { select: { id: true, requestDate: true, status: true } } } })
    if (!item) notFound()
    return (item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString(), borrowings: (item.borrowings ?? []).map(c => ({ ...c, requestDate: c.requestDate.toISOString() })) }))(item) as SerializedMember
  },
}
