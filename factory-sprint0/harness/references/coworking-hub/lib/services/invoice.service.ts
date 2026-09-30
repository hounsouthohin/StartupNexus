// AUTO-GÉNÉRÉ PAR dev_service_generator.py — NE PAS MODIFIER
import { notFound } from 'next/navigation'
import prisma from '@/lib/prisma'
import type { Invoice } from '@prisma/client'
import type { CreateInvoiceInput, UpdateInvoiceInput, SerializedInvoice } from '@/lib/types'

const _serialize = (item: Invoice): SerializedInvoice => {
  const { userId: _owner, ...rest } = item
  return ({
    ...rest,
  issueDate: rest.issueDate.toISOString(),
  createdAt: rest.createdAt.toISOString(),
  updatedAt: rest.updatedAt.toISOString(),
  }) as SerializedInvoice
}

export const invoiceService = {
  getAll: async (userId: string, page: number = 1, pageSize: number = 20): Promise<SerializedInvoice[]> => {
    const items = await prisma.invoice.findMany({ where: { userId }, select: { id: true, amount: true, issueDate: true, status: true, reservationId: true, createdAt: true, updatedAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, issueDate: item.issueDate.toISOString(), createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedInvoice[]
  },

  getAllAsAdmin: async (page: number = 1, pageSize: number = 20): Promise<SerializedInvoice[]> => {
    const items = await prisma.invoice.findMany({ select: { id: true, amount: true, issueDate: true, status: true, reservationId: true, createdAt: true, updatedAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, issueDate: item.issueDate.toISOString(), createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedInvoice[]
  },

  getByIdAsAdmin: async (id: string): Promise<SerializedInvoice> => {
    const item = await prisma.invoice.findFirst({ where: { id } })
    if (!item) notFound()
    return _serialize(item)
  },

  getById: async (userId: string, id: string): Promise<SerializedInvoice> => {
    const item = await prisma.invoice.findFirst({ where: { id, userId } })
    if (!item) notFound()
    return _serialize(item)
  },

  create: async (userId: string, data: CreateInvoiceInput): Promise<SerializedInvoice> => {
    if (data.reservationId) {
      const _owned_reservationId = await prisma.reservation.findFirst({ where: { id: data.reservationId, userId: userId }, select: { id: true } })
      if (!_owned_reservationId) throw new Error('Référence liée introuvable.')
    }
    const result = await prisma.invoice.create({
      data: { ...data, userId, status: 'pending' }
    })
    return _serialize(result)
  },

  update: async (userId: string, id: string, data: UpdateInvoiceInput): Promise<SerializedInvoice> => {
    if (data.reservationId) {
      const _owned_reservationId = await prisma.reservation.findFirst({ where: { id: data.reservationId, userId: userId }, select: { id: true } })
      if (!_owned_reservationId) throw new Error('Référence liée introuvable.')
    }
    if (data.status !== undefined) {
      const _cur = await prisma.invoice.findFirst({ where: { id, userId }, select: { status: true } })
      if (!_cur) notFound()
      if (data.status !== undefined && data.status !== _cur.status) {
        const _allowed: Record<string, string[]> = { overdue: [], paid: [], pending: ['paid', 'overdue'] }
        if (!(_allowed[_cur.status] ?? []).includes(data.status)) {
          throw new Error(`Transition interdite : ${_cur.status} → ${data.status}`)
        }
      }
    }
    const result = await prisma.invoice.update({
      where: { id, userId },
      data: { ...data }
    })
    return _serialize(result)
  },

  delete: async (userId: string, id: string): Promise<void> => {
    await prisma.invoice.delete({ where: { id, userId } })
  },

  getByReservationId: async (userId: string, reservationId: string, page: number = 1, pageSize: number = 20): Promise<SerializedInvoice[]> => {
    const items = await prisma.invoice.findMany({ where: { reservationId, userId: userId }, select: { id: true, amount: true, issueDate: true, status: true, reservationId: true, createdAt: true, updatedAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, issueDate: item.issueDate.toISOString(), createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedInvoice[]
  },

  getAllWithRelations: async (userId: string, page: number = 1, pageSize: number = 20): Promise<SerializedInvoice[]> => {
    const items = await prisma.invoice.findMany({ where: { userId }, select: { id: true, amount: true, issueDate: true, status: true, reservationId: true, createdAt: true, updatedAt: true, reservation: { select: { id: true, date: true, startTime: true, endTime: true, status: true } } }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, issueDate: item.issueDate.toISOString(), createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString(), reservation: item.reservation ? { ...item.reservation, date: item.reservation.date.toISOString(), startTime: item.reservation.startTime.toISOString(), endTime: item.reservation.endTime.toISOString() } : item.reservation })) as SerializedInvoice[]
  },

  getByIdWithRelations: async (userId: string, id: string): Promise<SerializedInvoice> => {
    const item = await prisma.invoice.findFirst({ where: { id, userId }, select: { id: true, amount: true, issueDate: true, status: true, reservationId: true, createdAt: true, updatedAt: true, reservation: { select: { id: true, date: true, startTime: true, endTime: true, status: true } } } })
    if (!item) notFound()
    return (item => ({ ...item, issueDate: item.issueDate.toISOString(), createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString(), reservation: item.reservation ? { ...item.reservation, date: item.reservation.date.toISOString(), startTime: item.reservation.startTime.toISOString(), endTime: item.reservation.endTime.toISOString() } : item.reservation }))(item) as SerializedInvoice
  },

  getByIdWithRelationsAsAdmin: async (id: string): Promise<SerializedInvoice> => {
    const item = await prisma.invoice.findFirst({ where: { id }, select: { id: true, amount: true, issueDate: true, status: true, reservationId: true, createdAt: true, updatedAt: true, reservation: { select: { id: true, date: true, startTime: true, endTime: true, status: true } } } })
    if (!item) notFound()
    return (item => ({ ...item, issueDate: item.issueDate.toISOString(), createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString(), reservation: item.reservation ? { ...item.reservation, date: item.reservation.date.toISOString(), startTime: item.reservation.startTime.toISOString(), endTime: item.reservation.endTime.toISOString() } : item.reservation }))(item) as SerializedInvoice
  },

  transitionTo: async (userId: string, id: string, newStatus: string, data: Partial<UpdateInvoiceInput> = {}): Promise<SerializedInvoice> => {
    const _cur = await prisma.invoice.findFirst({ where: { id }, select: { status: true } })
    if (!_cur) notFound()
    const _allowed: Record<string, string[]> = { overdue: [], paid: [], pending: ['paid', 'overdue'] }
    if (!(_allowed[_cur.status] ?? []).includes(newStatus)) {
      throw new Error(`Transition interdite : ${_cur.status} → ${newStatus}`)
    }
    // Seuls les champs déclarés pour l'état CIBLE sont écrits — jamais un champ
    // métier arbitraire (sinon transitionTo rouvrirait le verrou d'édition).
    const _fieldsByState: Record<string, string[]> = {}
    const _keep = new Set(_fieldsByState[newStatus] ?? [])
    const _payload: Partial<UpdateInvoiceInput> = {}
    for (const _k of Object.keys(data)) {
      if (_keep.has(_k) && (data as Record<string, unknown>)[_k] !== undefined) {
        (_payload as Record<string, unknown>)[_k] = (data as Record<string, unknown>)[_k]
      }
    }
    const result = await prisma.invoice.update({ where: { id }, data: { ..._payload, status: newStatus as Invoice['status'] } })
    return _serialize(result)
  },
}
