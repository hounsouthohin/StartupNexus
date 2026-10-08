// AUTO-GÉNÉRÉ PAR dev_service_generator.py — NE PAS MODIFIER
import { notFound } from 'next/navigation'
import prisma from '@/lib/prisma'
import type { Intervention } from '@prisma/client'
import type { CreateInterventionInput, UpdateInterventionInput, SerializedIntervention } from '@/lib/types'

const _serialize = (item: Intervention): SerializedIntervention => {
  const { userId: _owner, ...rest } = item
  return ({
    ...rest,
  date: rest.date.toISOString(),
  createdAt: rest.createdAt.toISOString(),
  updatedAt: rest.updatedAt.toISOString(),
  }) as SerializedIntervention
}

export const interventionService = {
  getAll: async (userId: string, page: number = 1, pageSize: number = 20): Promise<SerializedIntervention[]> => {
    const items = await prisma.intervention.findMany({ where: { userId }, select: { id: true, date: true, status: true, machineId: true, createdAt: true, updatedAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, date: item.date.toISOString(), createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedIntervention[]
  },

  getById: async (userId: string, id: string): Promise<SerializedIntervention> => {
    const item = await prisma.intervention.findFirst({ where: { id, userId } })
    if (!item) notFound()
    return _serialize(item)
  },

  create: async (userId: string, data: CreateInterventionInput): Promise<SerializedIntervention> => {
    if (data.machineId) {
      const _owned_machineId = await prisma.machine.findFirst({ where: { id: data.machineId, userId: userId }, select: { id: true } })
      if (!_owned_machineId) throw new Error('Référence liée introuvable.')
    }
    const result = await prisma.intervention.create({
      data: { ...data, userId, status: 'ouverte' }
    })
    return _serialize(result)
  },

  update: async (userId: string, id: string, data: UpdateInterventionInput): Promise<SerializedIntervention> => {
    if (data.machineId) {
      const _owned_machineId = await prisma.machine.findFirst({ where: { id: data.machineId, userId: userId }, select: { id: true } })
      if (!_owned_machineId) throw new Error('Référence liée introuvable.')
    }
    if (data.status !== undefined) {
      const _cur = await prisma.intervention.findFirst({ where: { id, userId }, select: { status: true } })
      if (!_cur) notFound()
      if (data.status !== undefined && data.status !== _cur.status) {
        const _allowed: Record<string, string[]> = { cloturee: ['payee'], en_cours: ['cloturee'], ouverte: ['en_cours'], payee: [] }
        if (!(_allowed[_cur.status] ?? []).includes(data.status)) {
          throw new Error(`Transition interdite : ${_cur.status} → ${data.status}`)
        }
      }
    }
    const result = await prisma.intervention.update({
      where: { id, userId },
      data: { ...data }
    })
    return _serialize(result)
  },

  delete: async (userId: string, id: string): Promise<void> => {
    await prisma.intervention.delete({ where: { id, userId } })
  },

  getByMachineId: async (userId: string, machineId: string, page: number = 1, pageSize: number = 20): Promise<SerializedIntervention[]> => {
    const items = await prisma.intervention.findMany({ where: { machineId, userId: userId }, select: { id: true, date: true, status: true, machineId: true, createdAt: true, updatedAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, date: item.date.toISOString(), createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedIntervention[]
  },

  getAllWithRelations: async (userId: string, page: number = 1, pageSize: number = 20): Promise<SerializedIntervention[]> => {
    const items = await prisma.intervention.findMany({ where: { userId }, select: { id: true, date: true, status: true, machineId: true, createdAt: true, updatedAt: true, machine: { select: { id: true, model: true, serialNumber: true, socket: true } }, actions: { select: { id: true, description: true, status: true } } }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, date: item.date.toISOString(), createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedIntervention[]
  },

  getByIdWithRelations: async (userId: string, id: string): Promise<SerializedIntervention> => {
    const item = await prisma.intervention.findFirst({ where: { id, userId }, select: { id: true, date: true, status: true, machineId: true, createdAt: true, updatedAt: true, machine: { select: { id: true, model: true, serialNumber: true, socket: true } }, actions: { select: { id: true, description: true, status: true } } } })
    if (!item) notFound()
    return (item => ({ ...item, date: item.date.toISOString(), createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() }))(item) as SerializedIntervention
  },

  transitionTo: async (userId: string, id: string, newStatus: string, data: Partial<UpdateInterventionInput> = {}): Promise<SerializedIntervention> => {
    const _cur = await prisma.intervention.findFirst({ where: { id, userId }, select: { status: true } })
    if (!_cur) notFound()
    const _allowed: Record<string, string[]> = { cloturee: ['payee'], en_cours: ['cloturee'], ouverte: ['en_cours'], payee: [] }
    if (!(_allowed[_cur.status] ?? []).includes(newStatus)) {
      throw new Error(`Transition interdite : ${_cur.status} → ${newStatus}`)
    }
    // Seuls les champs déclarés pour l'état CIBLE sont écrits — jamais un champ
    // métier arbitraire (sinon transitionTo rouvrirait le verrou d'édition).
    const _fieldsByState: Record<string, string[]> = {}
    const _keep = new Set(_fieldsByState[newStatus] ?? [])
    const _payload: Partial<UpdateInterventionInput> = {}
    for (const _k of Object.keys(data)) {
      if (_keep.has(_k) && (data as Record<string, unknown>)[_k] !== undefined) {
        (_payload as Record<string, unknown>)[_k] = (data as Record<string, unknown>)[_k]
      }
    }
    const result = await prisma.intervention.update({ where: { id, userId }, data: { ..._payload, status: newStatus as Intervention['status'] } })
    return _serialize(result)
  },
}
