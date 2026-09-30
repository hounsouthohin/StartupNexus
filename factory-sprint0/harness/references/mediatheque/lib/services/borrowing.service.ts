// AUTO-GÉNÉRÉ PAR dev_service_generator.py — NE PAS MODIFIER
import { notFound } from 'next/navigation'
import prisma from '@/lib/prisma'
import type { Borrowing } from '@prisma/client'
import type { CreateBorrowingInput, UpdateBorrowingInput, SerializedBorrowing } from '@/lib/types'

const _serialize = (item: Borrowing): SerializedBorrowing => {
  const { userId: _owner, ...rest } = item
  return ({
    ...rest,
  requestDate: rest.requestDate.toISOString(),
  createdAt: rest.createdAt.toISOString(),
  updatedAt: rest.updatedAt.toISOString(),
  }) as SerializedBorrowing
}

export const borrowingService = {
  getAll: async (userId: string, page: number = 1, pageSize: number = 20): Promise<SerializedBorrowing[]> => {
    const items = await prisma.borrowing.findMany({ where: { userId }, select: { id: true, requestDate: true, status: true, bookId: true, createdAt: true, updatedAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, requestDate: item.requestDate.toISOString(), createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedBorrowing[]
  },

  getAllAsAdmin: async (page: number = 1, pageSize: number = 20): Promise<SerializedBorrowing[]> => {
    const items = await prisma.borrowing.findMany({ select: { id: true, requestDate: true, status: true, bookId: true, createdAt: true, updatedAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, requestDate: item.requestDate.toISOString(), createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedBorrowing[]
  },

  getByIdAsAdmin: async (id: string): Promise<SerializedBorrowing> => {
    const item = await prisma.borrowing.findFirst({ where: { id } })
    if (!item) notFound()
    return _serialize(item)
  },

  getById: async (userId: string, id: string): Promise<SerializedBorrowing> => {
    const item = await prisma.borrowing.findFirst({ where: { id, userId } })
    if (!item) notFound()
    return _serialize(item)
  },

  create: async (userId: string, data: CreateBorrowingInput): Promise<SerializedBorrowing> => {
    if (data.bookId) {
      const _owned_bookId = await prisma.book.findFirst({ where: { id: data.bookId }, select: { id: true } })
      if (!_owned_bookId) throw new Error('Référence liée introuvable.')
    }
    const result = await prisma.borrowing.create({
      data: { ...data, userId, status: 'requested' }
    })
    return _serialize(result)
  },

  update: async (userId: string, id: string, data: UpdateBorrowingInput): Promise<SerializedBorrowing> => {
    if (data.bookId) {
      const _owned_bookId = await prisma.book.findFirst({ where: { id: data.bookId }, select: { id: true } })
      if (!_owned_bookId) throw new Error('Référence liée introuvable.')
    }
    if (data.status !== undefined) {
      const _cur = await prisma.borrowing.findFirst({ where: { id, userId }, select: { status: true } })
      if (!_cur) notFound()
      if (data.status !== undefined && data.status !== _cur.status) {
        const _allowed: Record<string, string[]> = { accepted: ['returned'], refused: [], requested: ['accepted', 'refused'], returned: [] }
        if (!(_allowed[_cur.status] ?? []).includes(data.status)) {
          throw new Error(`Transition interdite : ${_cur.status} → ${data.status}`)
        }
      }
    }
    const result = await prisma.borrowing.update({
      where: { id, userId },
      data: { ...data }
    })
    return _serialize(result)
  },

  delete: async (userId: string, id: string): Promise<void> => {
    await prisma.borrowing.delete({ where: { id, userId } })
  },

  getByBookId: async (userId: string, bookId: string, page: number = 1, pageSize: number = 20): Promise<SerializedBorrowing[]> => {
    const items = await prisma.borrowing.findMany({ where: { bookId, userId: userId }, select: { id: true, requestDate: true, status: true, bookId: true, createdAt: true, updatedAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, requestDate: item.requestDate.toISOString(), createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedBorrowing[]
  },

  getAllWithRelations: async (userId: string, page: number = 1, pageSize: number = 20): Promise<SerializedBorrowing[]> => {
    const items = await prisma.borrowing.findMany({ where: { userId }, select: { id: true, requestDate: true, status: true, bookId: true, createdAt: true, updatedAt: true, book: { select: { id: true, title: true, author: true, summary: true, genre: true } } }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, requestDate: item.requestDate.toISOString(), createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedBorrowing[]
  },

  getByIdWithRelations: async (userId: string, id: string): Promise<SerializedBorrowing> => {
    const item = await prisma.borrowing.findFirst({ where: { id, userId }, select: { id: true, requestDate: true, status: true, bookId: true, createdAt: true, updatedAt: true, book: { select: { id: true, title: true, author: true, summary: true, genre: true } } } })
    if (!item) notFound()
    return (item => ({ ...item, requestDate: item.requestDate.toISOString(), createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() }))(item) as SerializedBorrowing
  },

  getByIdWithRelationsAsAdmin: async (id: string): Promise<SerializedBorrowing> => {
    const item = await prisma.borrowing.findFirst({ where: { id }, select: { id: true, requestDate: true, status: true, bookId: true, createdAt: true, updatedAt: true, book: { select: { id: true, title: true, author: true, summary: true, genre: true } } } })
    if (!item) notFound()
    return (item => ({ ...item, requestDate: item.requestDate.toISOString(), createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() }))(item) as SerializedBorrowing
  },

  transitionTo: async (userId: string, id: string, newStatus: string, data: Partial<UpdateBorrowingInput> = {}): Promise<SerializedBorrowing> => {
    const _cur = await prisma.borrowing.findFirst({ where: { id }, select: { status: true } })
    if (!_cur) notFound()
    const _allowed: Record<string, string[]> = { accepted: ['returned'], refused: [], requested: ['accepted', 'refused'], returned: [] }
    if (!(_allowed[_cur.status] ?? []).includes(newStatus)) {
      throw new Error(`Transition interdite : ${_cur.status} → ${newStatus}`)
    }
    // Seuls les champs déclarés pour l'état CIBLE sont écrits — jamais un champ
    // métier arbitraire (sinon transitionTo rouvrirait le verrou d'édition).
    const _fieldsByState: Record<string, string[]> = {}
    const _keep = new Set(_fieldsByState[newStatus] ?? [])
    const _payload: Partial<UpdateBorrowingInput> = {}
    for (const _k of Object.keys(data)) {
      if (_keep.has(_k) && (data as Record<string, unknown>)[_k] !== undefined) {
        (_payload as Record<string, unknown>)[_k] = (data as Record<string, unknown>)[_k]
      }
    }
    const result = await prisma.borrowing.update({ where: { id }, data: { ..._payload, status: newStatus as Borrowing['status'] } })
    return _serialize(result)
  },
}
