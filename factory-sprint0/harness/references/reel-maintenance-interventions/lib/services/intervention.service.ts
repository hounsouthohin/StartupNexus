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
    const items = await prisma.intervention.findMany({ where: { userId }, select: { id: true, date: true, status: true, clientId: true, technicianId: true, createdAt: true, updatedAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, date: item.date.toISOString(), createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedIntervention[]
  },

  getAllAsAdmin: async (page: number = 1, pageSize: number = 20): Promise<SerializedIntervention[]> => {
    const items = await prisma.intervention.findMany({ select: { id: true, date: true, status: true, clientId: true, technicianId: true, createdAt: true, updatedAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, date: item.date.toISOString(), createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedIntervention[]
  },

  getByIdAsAdmin: async (id: string): Promise<SerializedIntervention> => {
    const item = await prisma.intervention.findFirst({ where: { id } })
    if (!item) notFound()
    return _serialize(item)
  },

  getById: async (userId: string, id: string): Promise<SerializedIntervention> => {
    const item = await prisma.intervention.findFirst({ where: { id, userId } })
    if (!item) notFound()
    return _serialize(item)
  },

  create: async (userId: string, data: CreateInterventionInput): Promise<SerializedIntervention> => {
    if (data.clientId) {
      const _owned_clientId = await prisma.client.findFirst({ where: { id: data.clientId, userId: userId }, select: { id: true } })
      if (!_owned_clientId) throw new Error('Référence liée introuvable.')
    }
    if (data.technicianId) {
      const _owned_technicianId = await prisma.technician.findFirst({ where: { id: data.technicianId, userId: userId }, select: { id: true } })
      if (!_owned_technicianId) throw new Error('Référence liée introuvable.')
    }
    const result = await prisma.intervention.create({
      data: { ...data, userId, status: 'planned' }
    })
    return _serialize(result)
  },

  update: async (userId: string, id: string, data: UpdateInterventionInput): Promise<SerializedIntervention> => {
    if (data.clientId) {
      const _owned_clientId = await prisma.client.findFirst({ where: { id: data.clientId, userId: userId }, select: { id: true } })
      if (!_owned_clientId) throw new Error('Référence liée introuvable.')
    }
    if (data.technicianId) {
      const _owned_technicianId = await prisma.technician.findFirst({ where: { id: data.technicianId, userId: userId }, select: { id: true } })
      if (!_owned_technicianId) throw new Error('Référence liée introuvable.')
    }
    const _cur = await prisma.intervention.findFirst({ where: { id, userId }, select: { status: true } })
    if (!_cur) notFound()
    if ((['cancelled', 'completed'] as string[]).includes(_cur.status)) {
      const _touched = Object.keys(data).filter(_k => _k !== 'status' && (data as Record<string, unknown>)[_k] !== undefined)
      if (_touched.length > 0) {
        throw new Error(`Cette fiche n'est plus modifiable dans son état actuel.`)
      }
    }
    if (data.status !== undefined && data.status !== _cur.status) {
      const _allowed: Record<string, string[]> = { cancelled: [], completed: [], confirmed: ['completed', 'cancelled'], planned: ['confirmed', 'cancelled'] }
      if (!(_allowed[_cur.status] ?? []).includes(data.status)) {
        throw new Error(`Transition interdite : ${_cur.status} → ${data.status}`)
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

  getByClientId: async (userId: string, clientId: string, page: number = 1, pageSize: number = 20): Promise<SerializedIntervention[]> => {
    const items = await prisma.intervention.findMany({ where: { clientId, userId: userId }, select: { id: true, date: true, status: true, clientId: true, technicianId: true, createdAt: true, updatedAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, date: item.date.toISOString(), createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedIntervention[]
  },

  getByTechnicianId: async (userId: string, technicianId: string, page: number = 1, pageSize: number = 20): Promise<SerializedIntervention[]> => {
    const items = await prisma.intervention.findMany({ where: { technicianId, userId: userId }, select: { id: true, date: true, status: true, clientId: true, technicianId: true, createdAt: true, updatedAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, date: item.date.toISOString(), createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedIntervention[]
  },

  getAllWithRelations: async (userId: string, page: number = 1, pageSize: number = 20): Promise<SerializedIntervention[]> => {
    const items = await prisma.intervention.findMany({ where: { userId }, select: { id: true, date: true, status: true, clientId: true, technicianId: true, createdAt: true, updatedAt: true, client: { select: { id: true, name: true, email: true, phone: true, address: true } }, technician: { select: { id: true, name: true, email: true, phone: true, region: true } } }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, date: item.date.toISOString(), createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedIntervention[]
  },

  getByIdWithRelations: async (userId: string, id: string): Promise<SerializedIntervention> => {
    const item = await prisma.intervention.findFirst({ where: { id, userId }, select: { id: true, date: true, status: true, clientId: true, technicianId: true, createdAt: true, updatedAt: true, client: { select: { id: true, name: true, email: true, phone: true, address: true } }, technician: { select: { id: true, name: true, email: true, phone: true, region: true } } } })
    if (!item) notFound()
    return (item => ({ ...item, date: item.date.toISOString(), createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() }))(item) as SerializedIntervention
  },

  getByIdWithRelationsAsAdmin: async (id: string): Promise<SerializedIntervention> => {
    const item = await prisma.intervention.findFirst({ where: { id }, select: { id: true, date: true, status: true, clientId: true, technicianId: true, createdAt: true, updatedAt: true, client: { select: { id: true, name: true, email: true, phone: true, address: true } }, technician: { select: { id: true, name: true, email: true, phone: true, region: true } } } })
    if (!item) notFound()
    return (item => ({ ...item, date: item.date.toISOString(), createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() }))(item) as SerializedIntervention
  },

  transitionTo: async (userId: string, id: string, newStatus: string, data: Partial<UpdateInterventionInput> = {}): Promise<SerializedIntervention> => {
    const _cur = await prisma.intervention.findFirst({ where: { id }, select: { status: true } })
    if (!_cur) notFound()
    const _allowed: Record<string, string[]> = { cancelled: [], completed: [], confirmed: ['completed', 'cancelled'], planned: ['confirmed', 'cancelled'] }
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
    const result = await prisma.intervention.update({ where: { id }, data: { ..._payload, status: newStatus as Intervention['status'] } })
    return _serialize(result)
  },
}
