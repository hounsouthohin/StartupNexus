// AUTO-GÉNÉRÉ PAR dev_service_generator.py — NE PAS MODIFIER
import { notFound } from 'next/navigation'
import prisma from '@/lib/prisma'
import type { Reservation } from '@prisma/client'
import type { CreateReservationInput, UpdateReservationInput, SerializedReservation } from '@/lib/types'

const _serialize = (item: Reservation): SerializedReservation => {
  const { userId: _owner, ...rest } = item
  return ({
    ...rest,
  date: rest.date.toISOString(),
  startTime: rest.startTime.toISOString(),
  endTime: rest.endTime.toISOString(),
  createdAt: rest.createdAt.toISOString(),
  updatedAt: rest.updatedAt.toISOString(),
  }) as SerializedReservation
}

export const reservationService = {
  getAll: async (userId: string, page: number = 1, pageSize: number = 20): Promise<SerializedReservation[]> => {
    const items = await prisma.reservation.findMany({ where: { userId }, select: { id: true, date: true, startTime: true, endTime: true, status: true, reason: true, spaceId: true, memberId: true, createdAt: true, updatedAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, date: item.date.toISOString(), startTime: item.startTime.toISOString(), endTime: item.endTime.toISOString(), createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedReservation[]
  },

  getAllAsAdmin: async (page: number = 1, pageSize: number = 20): Promise<SerializedReservation[]> => {
    const items = await prisma.reservation.findMany({ select: { id: true, date: true, startTime: true, endTime: true, status: true, reason: true, spaceId: true, memberId: true, createdAt: true, updatedAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, date: item.date.toISOString(), startTime: item.startTime.toISOString(), endTime: item.endTime.toISOString(), createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedReservation[]
  },

  getByIdAsAdmin: async (id: string): Promise<SerializedReservation> => {
    const item = await prisma.reservation.findFirst({ where: { id } })
    if (!item) notFound()
    return _serialize(item)
  },

  getById: async (userId: string, id: string): Promise<SerializedReservation> => {
    const item = await prisma.reservation.findFirst({ where: { id, userId } })
    if (!item) notFound()
    return _serialize(item)
  },

  create: async (userId: string, data: CreateReservationInput): Promise<SerializedReservation> => {
    if (data.spaceId) {
      const _owned_spaceId = await prisma.space.findFirst({ where: { id: data.spaceId }, select: { id: true } })
      if (!_owned_spaceId) throw new Error('Référence liée introuvable.')
    }
    if (data.memberId) {
      const _owned_memberId = await prisma.member.findFirst({ where: { id: data.memberId, userId: userId }, select: { id: true } })
      if (!_owned_memberId) throw new Error('Référence liée introuvable.')
    }
    const result = await prisma.reservation.create({
      data: { ...data, userId, status: 'requested' }
    })
    return _serialize(result)
  },

  update: async (userId: string, id: string, data: UpdateReservationInput): Promise<SerializedReservation> => {
    if (data.spaceId) {
      const _owned_spaceId = await prisma.space.findFirst({ where: { id: data.spaceId }, select: { id: true } })
      if (!_owned_spaceId) throw new Error('Référence liée introuvable.')
    }
    if (data.memberId) {
      const _owned_memberId = await prisma.member.findFirst({ where: { id: data.memberId, userId: userId }, select: { id: true } })
      if (!_owned_memberId) throw new Error('Référence liée introuvable.')
    }
    if (data.status !== undefined) {
      const _cur = await prisma.reservation.findFirst({ where: { id, userId }, select: { status: true } })
      if (!_cur) notFound()
      if (data.status !== undefined && data.status !== _cur.status) {
        const _allowed: Record<string, string[]> = { cancelled: [], completed: [], confirmed: ['completed', 'cancelled'], refused: [], requested: ['confirmed', 'refused'] }
        if (!(_allowed[_cur.status] ?? []).includes(data.status)) {
          throw new Error(`Transition interdite : ${_cur.status} → ${data.status}`)
        }
      }
    }
    const result = await prisma.reservation.update({
      where: { id, userId },
      data: { ...data }
    })
    return _serialize(result)
  },

  delete: async (userId: string, id: string): Promise<void> => {
    await prisma.reservation.delete({ where: { id, userId } })
  },

  getBySpaceId: async (userId: string, spaceId: string, page: number = 1, pageSize: number = 20): Promise<SerializedReservation[]> => {
    const items = await prisma.reservation.findMany({ where: { spaceId, userId: userId }, select: { id: true, date: true, startTime: true, endTime: true, status: true, reason: true, spaceId: true, memberId: true, createdAt: true, updatedAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, date: item.date.toISOString(), startTime: item.startTime.toISOString(), endTime: item.endTime.toISOString(), createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedReservation[]
  },

  getByMemberId: async (userId: string, memberId: string, page: number = 1, pageSize: number = 20): Promise<SerializedReservation[]> => {
    const items = await prisma.reservation.findMany({ where: { memberId, userId: userId }, select: { id: true, date: true, startTime: true, endTime: true, status: true, reason: true, spaceId: true, memberId: true, createdAt: true, updatedAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, date: item.date.toISOString(), startTime: item.startTime.toISOString(), endTime: item.endTime.toISOString(), createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedReservation[]
  },

  getAllWithRelations: async (userId: string, page: number = 1, pageSize: number = 20): Promise<SerializedReservation[]> => {
    const items = await prisma.reservation.findMany({ where: { userId }, select: { id: true, date: true, startTime: true, endTime: true, status: true, reason: true, spaceId: true, memberId: true, createdAt: true, updatedAt: true, space: { select: { id: true, name: true, description: true, type: true, capacity: true } }, member: { select: { id: true, name: true, email: true, company: true, phone: true } }, invoice: { select: { id: true, amount: true, issueDate: true, status: true } } }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, date: item.date.toISOString(), startTime: item.startTime.toISOString(), endTime: item.endTime.toISOString(), createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString(), invoice: item.invoice ? { ...item.invoice, issueDate: item.invoice.issueDate.toISOString() } : item.invoice })) as SerializedReservation[]
  },

  getByIdWithRelations: async (userId: string, id: string): Promise<SerializedReservation> => {
    const item = await prisma.reservation.findFirst({ where: { id, userId }, select: { id: true, date: true, startTime: true, endTime: true, status: true, reason: true, spaceId: true, memberId: true, createdAt: true, updatedAt: true, space: { select: { id: true, name: true, description: true, type: true, capacity: true } }, member: { select: { id: true, name: true, email: true, company: true, phone: true } }, invoice: { select: { id: true, amount: true, issueDate: true, status: true } } } })
    if (!item) notFound()
    return (item => ({ ...item, date: item.date.toISOString(), startTime: item.startTime.toISOString(), endTime: item.endTime.toISOString(), createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString(), invoice: item.invoice ? { ...item.invoice, issueDate: item.invoice.issueDate.toISOString() } : item.invoice }))(item) as SerializedReservation
  },

  getByIdWithRelationsAsAdmin: async (id: string): Promise<SerializedReservation> => {
    const item = await prisma.reservation.findFirst({ where: { id }, select: { id: true, date: true, startTime: true, endTime: true, status: true, reason: true, spaceId: true, memberId: true, createdAt: true, updatedAt: true, space: { select: { id: true, name: true, description: true, type: true, capacity: true } }, member: { select: { id: true, name: true, email: true, company: true, phone: true } }, invoice: { select: { id: true, amount: true, issueDate: true, status: true } } } })
    if (!item) notFound()
    return (item => ({ ...item, date: item.date.toISOString(), startTime: item.startTime.toISOString(), endTime: item.endTime.toISOString(), createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString(), invoice: item.invoice ? { ...item.invoice, issueDate: item.invoice.issueDate.toISOString() } : item.invoice }))(item) as SerializedReservation
  },

  transitionTo: async (userId: string, id: string, newStatus: string, data: Partial<UpdateReservationInput> = {}): Promise<SerializedReservation> => {
    const _cur = await prisma.reservation.findFirst({ where: { id }, select: { status: true } })
    if (!_cur) notFound()
    const _allowed: Record<string, string[]> = { cancelled: [], completed: [], confirmed: ['completed', 'cancelled'], refused: [], requested: ['confirmed', 'refused'] }
    if (!(_allowed[_cur.status] ?? []).includes(newStatus)) {
      throw new Error(`Transition interdite : ${_cur.status} → ${newStatus}`)
    }
    // Seuls les champs déclarés pour l'état CIBLE sont écrits — jamais un champ
    // métier arbitraire (sinon transitionTo rouvrirait le verrou d'édition).
    const _fieldsByState: Record<string, string[]> = { refused: ['reason'] }
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
