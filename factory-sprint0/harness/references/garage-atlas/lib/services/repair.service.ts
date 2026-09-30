// AUTO-GÉNÉRÉ PAR dev_service_generator.py — NE PAS MODIFIER
import { notFound } from 'next/navigation'
import prisma from '@/lib/prisma'
import type { Repair } from '@prisma/client'
import type { CreateRepairInput, UpdateRepairInput, SerializedRepair } from '@/lib/types'

const _serialize = (item: Repair): SerializedRepair => {
  const { userId: _owner, ...rest } = item
  return ({
    ...rest,
  createdAt: rest.createdAt.toISOString(),
  updatedAt: rest.updatedAt.toISOString(),
  }) as SerializedRepair
}

export const repairService = {
  getAll: async (userId: string, page: number = 1, pageSize: number = 20): Promise<SerializedRepair[]> => {
    const items = await prisma.repair.findMany({ where: { userId }, select: { id: true, description: true, status: true, reasonForRejection: true, amountCharged: true, vehicleId: true, createdAt: true, updatedAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedRepair[]
  },

  getAllAsAdmin: async (page: number = 1, pageSize: number = 20): Promise<SerializedRepair[]> => {
    const items = await prisma.repair.findMany({ select: { id: true, description: true, status: true, reasonForRejection: true, amountCharged: true, vehicleId: true, createdAt: true, updatedAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedRepair[]
  },

  getByIdAsAdmin: async (id: string): Promise<SerializedRepair> => {
    const item = await prisma.repair.findFirst({ where: { id } })
    if (!item) notFound()
    return _serialize(item)
  },

  getById: async (userId: string, id: string): Promise<SerializedRepair> => {
    const item = await prisma.repair.findFirst({ where: { id, userId } })
    if (!item) notFound()
    return _serialize(item)
  },

  create: async (userId: string, data: CreateRepairInput): Promise<SerializedRepair> => {
    if (data.vehicleId) {
      const _owned_vehicleId = await prisma.vehicle.findFirst({ where: { id: data.vehicleId, userId: userId }, select: { id: true } })
      if (!_owned_vehicleId) throw new Error('Référence liée introuvable.')
    }
    const result = await prisma.repair.create({
      data: { ...data, userId, status: 'pending' }
    })
    return _serialize(result)
  },

  update: async (userId: string, id: string, data: UpdateRepairInput): Promise<SerializedRepair> => {
    if (data.vehicleId) {
      const _owned_vehicleId = await prisma.vehicle.findFirst({ where: { id: data.vehicleId, userId: userId }, select: { id: true } })
      if (!_owned_vehicleId) throw new Error('Référence liée introuvable.')
    }
    if (data.status !== undefined) {
      const _cur = await prisma.repair.findFirst({ where: { id, userId }, select: { status: true } })
      if (!_cur) notFound()
      if (data.status !== undefined && data.status !== _cur.status) {
        const _allowed: Record<string, string[]> = { accepted: ['in_progress'], completed: [], in_progress: ['completed'], pending: ['accepted', 'rejected'], rejected: [] }
        if (!(_allowed[_cur.status] ?? []).includes(data.status)) {
          throw new Error(`Transition interdite : ${_cur.status} → ${data.status}`)
        }
      }
    }
    const result = await prisma.repair.update({
      where: { id, userId },
      data: { ...data }
    })
    return _serialize(result)
  },

  delete: async (userId: string, id: string): Promise<void> => {
    await prisma.repair.delete({ where: { id, userId } })
  },

  getByVehicleId: async (userId: string, vehicleId: string, page: number = 1, pageSize: number = 20): Promise<SerializedRepair[]> => {
    const items = await prisma.repair.findMany({ where: { vehicleId, userId: userId }, select: { id: true, description: true, status: true, reasonForRejection: true, amountCharged: true, vehicleId: true, createdAt: true, updatedAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedRepair[]
  },

  getAllWithRelations: async (userId: string, page: number = 1, pageSize: number = 20): Promise<SerializedRepair[]> => {
    const items = await prisma.repair.findMany({ where: { userId }, select: { id: true, description: true, status: true, reasonForRejection: true, amountCharged: true, vehicleId: true, createdAt: true, updatedAt: true, vehicle: { select: { id: true, brand: true, model: true, licensePlate: true } } }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedRepair[]
  },

  getByIdWithRelations: async (userId: string, id: string): Promise<SerializedRepair> => {
    const item = await prisma.repair.findFirst({ where: { id, userId }, select: { id: true, description: true, status: true, reasonForRejection: true, amountCharged: true, vehicleId: true, createdAt: true, updatedAt: true, vehicle: { select: { id: true, brand: true, model: true, licensePlate: true } } } })
    if (!item) notFound()
    return (item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() }))(item) as SerializedRepair
  },

  getByIdWithRelationsAsAdmin: async (id: string): Promise<SerializedRepair> => {
    const item = await prisma.repair.findFirst({ where: { id }, select: { id: true, description: true, status: true, reasonForRejection: true, amountCharged: true, vehicleId: true, createdAt: true, updatedAt: true, vehicle: { select: { id: true, brand: true, model: true, licensePlate: true } } } })
    if (!item) notFound()
    return (item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() }))(item) as SerializedRepair
  },

  transitionTo: async (userId: string, id: string, newStatus: string, data: Partial<UpdateRepairInput> = {}): Promise<SerializedRepair> => {
    const _cur = await prisma.repair.findFirst({ where: { id }, select: { status: true } })
    if (!_cur) notFound()
    const _allowed: Record<string, string[]> = { accepted: ['in_progress'], completed: [], in_progress: ['completed'], pending: ['accepted', 'rejected'], rejected: [] }
    if (!(_allowed[_cur.status] ?? []).includes(newStatus)) {
      throw new Error(`Transition interdite : ${_cur.status} → ${newStatus}`)
    }
    // Seuls les champs déclarés pour l'état CIBLE sont écrits — jamais un champ
    // métier arbitraire (sinon transitionTo rouvrirait le verrou d'édition).
    const _fieldsByState: Record<string, string[]> = { completed: ['amountCharged'], rejected: ['reasonForRejection'] }
    const _keep = new Set(_fieldsByState[newStatus] ?? [])
    const _payload: Partial<UpdateRepairInput> = {}
    for (const _k of Object.keys(data)) {
      if (_keep.has(_k) && (data as Record<string, unknown>)[_k] !== undefined) {
        (_payload as Record<string, unknown>)[_k] = (data as Record<string, unknown>)[_k]
      }
    }
    const result = await prisma.repair.update({ where: { id }, data: { ..._payload, status: newStatus as Repair['status'] } })
    return _serialize(result)
  },
}
