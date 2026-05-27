// AUTO-GÉNÉRÉ PAR dev_service_generator.py — NE PAS MODIFIER
import { notFound } from 'next/navigation'
import prisma from '@/lib/prisma'
import type { LeaveRequest } from '@prisma/client'
import type { CreateLeaveRequestInput, UpdateLeaveRequestInput, SerializedLeaveRequest } from '@/lib/types'

const _serialize = (item: LeaveRequest): SerializedLeaveRequest => {
  const { userId: _owner, ...rest } = item
  return ({
    ...rest,
  startDate: rest.startDate.toISOString(),
  endDate: rest.endDate.toISOString(),
  createdAt: rest.createdAt.toISOString(),
  }) as SerializedLeaveRequest
}

export const leaveRequestService = {
  getAll: async (userId: string, page: number = 1, pageSize: number = 20): Promise<SerializedLeaveRequest[]> => {
    const items = await prisma.leaveRequest.findMany({ where: { userId }, select: { id: true, startDate: true, endDate: true, reason: true, type: true, status: true, createdAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, startDate: item.startDate.toISOString(), endDate: item.endDate.toISOString(), createdAt: item.createdAt.toISOString() })) as SerializedLeaveRequest[]
  },

  getById: async (userId: string, id: string): Promise<SerializedLeaveRequest> => {
    const item = await prisma.leaveRequest.findFirst({ where: { id, userId } })
    if (!item) notFound()
    return _serialize(item)
  },

  create: async (userId: string, data: CreateLeaveRequestInput): Promise<LeaveRequest> => {
    return prisma.leaveRequest.create({
      data: { ...data, userId }
    })
  },

  update: async (userId: string, id: string, data: UpdateLeaveRequestInput): Promise<LeaveRequest> => {
    return prisma.leaveRequest.update({
      where: { id, userId },
      data: { ...data }
    })
  },

  delete: async (userId: string, id: string): Promise<void> => {
    await prisma.leaveRequest.delete({ where: { id, userId } })
  },
}
