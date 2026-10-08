// AUTO-GÉNÉRÉ PAR dev_service_generator.py — NE PAS MODIFIER
import { notFound } from 'next/navigation'
import prisma from '@/lib/prisma'
import type { Reservation } from '@prisma/client'
import type { CreateReservationInput, UpdateReservationInput, SerializedReservation } from '@/lib/types'

const _serialize = (item: Reservation): SerializedReservation => {
  const { clientId: _owner, ...rest } = item
  return ({
    ...rest,
  date: rest.date.toISOString(),
  createdAt: rest.createdAt.toISOString(),
  updatedAt: rest.updatedAt.toISOString(),
  }) as SerializedReservation
}

export const reservationService = {
  getAll: async (clientId: string, page: number = 1, pageSize: number = 20): Promise<SerializedReservation[]> => {
    const items = await prisma.reservation.findMany({ where: { clientId }, select: { id: true, date: true, status: true, providerId: true, managerId: true, createdAt: true, updatedAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, date: item.date.toISOString(), createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedReservation[]
  },

  getAllAsAdmin: async (page: number = 1, pageSize: number = 20): Promise<SerializedReservation[]> => {
    const items = await prisma.reservation.findMany({ select: { id: true, date: true, status: true, providerId: true, managerId: true, createdAt: true, updatedAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, date: item.date.toISOString(), createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedReservation[]
  },

  getByIdAsAdmin: async (id: string): Promise<SerializedReservation> => {
    const item = await prisma.reservation.findFirst({ where: { id } })
    if (!item) notFound()
    return _serialize(item)
  },

  getById: async (clientId: string, id: string): Promise<SerializedReservation> => {
    const item = await prisma.reservation.findFirst({ where: { id, clientId } })
    if (!item) notFound()
    return _serialize(item)
  },

  create: async (clientId: string, data: CreateReservationInput): Promise<SerializedReservation> => {
    if (data.providerId) {
      const _owned_providerId = await prisma.provider.findFirst({ where: { id: data.providerId }, select: { id: true } })
      if (!_owned_providerId) throw new Error('Référence liée introuvable.')
    }
    if (data.managerId) {
      const _owned_managerId = await prisma.manager.findFirst({ where: { id: data.managerId }, select: { id: true } })
      if (!_owned_managerId) throw new Error('Référence liée introuvable.')
    }
    const result = await prisma.reservation.create({
      data: { ...data, clientId, status: 'pending' }
    })
    return _serialize(result)
  },

  update: async (clientId: string, id: string, data: UpdateReservationInput): Promise<SerializedReservation> => {
    if (data.providerId) {
      const _owned_providerId = await prisma.provider.findFirst({ where: { id: data.providerId }, select: { id: true } })
      if (!_owned_providerId) throw new Error('Référence liée introuvable.')
    }
    if (data.managerId) {
      const _owned_managerId = await prisma.manager.findFirst({ where: { id: data.managerId }, select: { id: true } })
      if (!_owned_managerId) throw new Error('Référence liée introuvable.')
    }
    if (data.status !== undefined) {
      const _cur = await prisma.reservation.findFirst({ where: { id, clientId }, select: { status: true } })
      if (!_cur) notFound()
      if (data.status !== undefined && data.status !== _cur.status) {
        const _allowed: Record<string, string[]> = { cancelled: [], confirmed: ['cancelled'], pending: ['confirmed', 'cancelled'] }
        if (!(_allowed[_cur.status] ?? []).includes(data.status)) {
          throw new Error(`Transition interdite : ${_cur.status} → ${data.status}`)
        }
      }
    }
    const result = await prisma.reservation.update({
      where: { id, clientId },
      data: { ...data }
    })
    return _serialize(result)
  },

  delete: async (clientId: string, id: string): Promise<void> => {
    await prisma.reservation.delete({ where: { id, clientId } })
  },

  getByProviderId: async (userId: string, providerId: string, page: number = 1, pageSize: number = 20): Promise<SerializedReservation[]> => {
    const items = await prisma.reservation.findMany({ where: { providerId, clientId: userId }, select: { id: true, date: true, status: true, providerId: true, managerId: true, createdAt: true, updatedAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, date: item.date.toISOString(), createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedReservation[]
  },

  getByManagerId: async (userId: string, managerId: string, page: number = 1, pageSize: number = 20): Promise<SerializedReservation[]> => {
    const items = await prisma.reservation.findMany({ where: { managerId, clientId: userId }, select: { id: true, date: true, status: true, providerId: true, managerId: true, createdAt: true, updatedAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, date: item.date.toISOString(), createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedReservation[]
  },

  getAllWithRelations: async (clientId: string, page: number = 1, pageSize: number = 20): Promise<SerializedReservation[]> => {
    const items = await prisma.reservation.findMany({ where: { clientId }, select: { id: true, date: true, status: true, providerId: true, managerId: true, createdAt: true, updatedAt: true, client: { select: { id: true, name: true, email: true } }, provider: { select: { id: true, name: true, email: true } }, manager: { select: { id: true, name: true, email: true } } }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, date: item.date.toISOString(), createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedReservation[]
  },

  getByIdWithRelations: async (clientId: string, id: string): Promise<SerializedReservation> => {
    const item = await prisma.reservation.findFirst({ where: { id, clientId }, select: { id: true, date: true, status: true, providerId: true, managerId: true, createdAt: true, updatedAt: true, client: { select: { id: true, name: true, email: true } }, provider: { select: { id: true, name: true, email: true } }, manager: { select: { id: true, name: true, email: true } } } })
    if (!item) notFound()
    return (item => ({ ...item, date: item.date.toISOString(), createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() }))(item) as SerializedReservation
  },

  getByIdWithRelationsAsAdmin: async (id: string): Promise<SerializedReservation> => {
    const item = await prisma.reservation.findFirst({ where: { id }, select: { id: true, date: true, status: true, providerId: true, managerId: true, createdAt: true, updatedAt: true, client: { select: { id: true, name: true, email: true } }, provider: { select: { id: true, name: true, email: true } }, manager: { select: { id: true, name: true, email: true } } } })
    if (!item) notFound()
    return (item => ({ ...item, date: item.date.toISOString(), createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() }))(item) as SerializedReservation
  },

  transitionTo: async (clientId: string, id: string, newStatus: string, data: Partial<UpdateReservationInput> = {}): Promise<SerializedReservation> => {
    const _cur = await prisma.reservation.findFirst({ where: { id }, select: { status: true } })
    if (!_cur) notFound()
    const _allowed: Record<string, string[]> = { cancelled: [], confirmed: ['cancelled'], pending: ['confirmed', 'cancelled'] }
    if (!(_allowed[_cur.status] ?? []).includes(newStatus)) {
      throw new Error(`Transition interdite : ${_cur.status} → ${newStatus}`)
    }
    // Seuls les champs déclarés pour l'état CIBLE sont écrits — jamais un champ
    // métier arbitraire (sinon transitionTo rouvrirait le verrou d'édition).
    const _fieldsByState: Record<string, string[]> = {}
    const _keep = new Set(_fieldsByState[newStatus] ?? [])
    const _payload: Partial<UpdateReservationInput> = {}
    for (const _k of Object.keys(data)) {
      if (_keep.has(_k) && (data as Record<string, unknown>)[_k] !== undefined) {
        (_payload as Record<string, unknown>)[_k] = (data as Record<string, unknown>)[_k]
      }
    }
    const result = await prisma.reservation.update({ where: { id }, data: { ..._payload, status: newStatus as Reservation['status'] } })
    return _serialize(result)
  },
}
