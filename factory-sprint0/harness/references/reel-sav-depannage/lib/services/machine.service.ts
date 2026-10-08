// AUTO-GÉNÉRÉ PAR dev_service_generator.py — NE PAS MODIFIER
import { notFound } from 'next/navigation'
import prisma from '@/lib/prisma'
import type { Machine } from '@prisma/client'
import type { CreateMachineInput, UpdateMachineInput, SerializedMachine } from '@/lib/types'

const _serialize = (item: Machine): SerializedMachine => {
  const { userId: _owner, ...rest } = item
  return ({
    ...rest,
  createdAt: rest.createdAt.toISOString(),
  updatedAt: rest.updatedAt.toISOString(),
  }) as SerializedMachine
}

export const machineService = {
  getAll: async (userId: string, page: number = 1, pageSize: number = 20): Promise<SerializedMachine[]> => {
    const items = await prisma.machine.findMany({ where: { userId }, select: { id: true, model: true, serialNumber: true, socket: true, clientId: true, createdAt: true, updatedAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedMachine[]
  },

  getById: async (userId: string, id: string): Promise<SerializedMachine> => {
    const item = await prisma.machine.findFirst({ where: { id, userId } })
    if (!item) notFound()
    return _serialize(item)
  },

  create: async (userId: string, data: CreateMachineInput): Promise<SerializedMachine> => {
    if (data.clientId) {
      const _owned_clientId = await prisma.client.findFirst({ where: { id: data.clientId, userId: userId }, select: { id: true } })
      if (!_owned_clientId) throw new Error('Référence liée introuvable.')
    }
    const result = await prisma.machine.create({
      data: { ...data, userId }
    })
    return _serialize(result)
  },

  update: async (userId: string, id: string, data: UpdateMachineInput): Promise<SerializedMachine> => {
    if (data.clientId) {
      const _owned_clientId = await prisma.client.findFirst({ where: { id: data.clientId, userId: userId }, select: { id: true } })
      if (!_owned_clientId) throw new Error('Référence liée introuvable.')
    }
    const result = await prisma.machine.update({
      where: { id, userId },
      data: { ...data }
    })
    return _serialize(result)
  },

  delete: async (userId: string, id: string): Promise<void> => {
    await prisma.machine.delete({ where: { id, userId } })
  },

  getByClientId: async (userId: string, clientId: string, page: number = 1, pageSize: number = 20): Promise<SerializedMachine[]> => {
    const items = await prisma.machine.findMany({ where: { clientId, userId: userId }, select: { id: true, model: true, serialNumber: true, socket: true, clientId: true, createdAt: true, updatedAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedMachine[]
  },

  getAllWithRelations: async (userId: string, page: number = 1, pageSize: number = 20): Promise<SerializedMachine[]> => {
    const items = await prisma.machine.findMany({ where: { userId }, select: { id: true, model: true, serialNumber: true, socket: true, clientId: true, createdAt: true, updatedAt: true, client: { select: { id: true, name: true, email: true, address: true } }, interventions: { select: { id: true, date: true, status: true } } }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString(), interventions: (item.interventions ?? []).map(c => ({ ...c, date: c.date.toISOString() })) })) as SerializedMachine[]
  },

  getByIdWithRelations: async (userId: string, id: string): Promise<SerializedMachine> => {
    const item = await prisma.machine.findFirst({ where: { id, userId }, select: { id: true, model: true, serialNumber: true, socket: true, clientId: true, createdAt: true, updatedAt: true, client: { select: { id: true, name: true, email: true, address: true } }, interventions: { select: { id: true, date: true, status: true } } } })
    if (!item) notFound()
    return (item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString(), interventions: (item.interventions ?? []).map(c => ({ ...c, date: c.date.toISOString() })) }))(item) as SerializedMachine
  },
}
