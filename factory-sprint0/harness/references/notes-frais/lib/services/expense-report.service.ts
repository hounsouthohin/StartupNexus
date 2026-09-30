// AUTO-GÉNÉRÉ PAR dev_service_generator.py — NE PAS MODIFIER
import { notFound } from 'next/navigation'
import prisma from '@/lib/prisma'
import type { ExpenseReport } from '@prisma/client'
import type { CreateExpenseReportInput, UpdateExpenseReportInput, SerializedExpenseReport } from '@/lib/types'

const _serialize = (item: ExpenseReport): SerializedExpenseReport => {
  const { userId: _owner, ...rest } = item
  return ({
    ...rest,
  expenseDate: rest.expenseDate.toISOString(),
  createdAt: rest.createdAt.toISOString(),
  updatedAt: rest.updatedAt.toISOString(),
  }) as SerializedExpenseReport
}

export const expenseReportService = {
  getAll: async (userId: string, page: number = 1, pageSize: number = 20): Promise<SerializedExpenseReport[]> => {
    const items = await prisma.expenseReport.findMany({ where: { userId }, select: { id: true, title: true, amount: true, expenseDate: true, category: true, description: true, status: true, rejectionReason: true, createdAt: true, updatedAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, expenseDate: item.expenseDate.toISOString(), createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedExpenseReport[]
  },

  getById: async (userId: string, id: string): Promise<SerializedExpenseReport> => {
    const item = await prisma.expenseReport.findFirst({ where: { id, userId } })
    if (!item) notFound()
    return _serialize(item)
  },

  create: async (userId: string, data: CreateExpenseReportInput): Promise<SerializedExpenseReport> => {
    const result = await prisma.expenseReport.create({
      data: { ...data, userId, status: 'draft' }
    })
    return _serialize(result)
  },

  update: async (userId: string, id: string, data: UpdateExpenseReportInput): Promise<SerializedExpenseReport> => {
    const _cur = await prisma.expenseReport.findFirst({ where: { id, userId }, select: { status: true } })
    if (!_cur) notFound()
    if ((['approved', 'refused', 'reimbursed', 'submitted'] as string[]).includes(_cur.status)) {
      const _touched = Object.keys(data).filter(_k => _k !== 'status' && (data as Record<string, unknown>)[_k] !== undefined)
      if (_touched.length > 0) {
        throw new Error(`Cette fiche n'est plus modifiable dans son état actuel.`)
      }
    }
    if (data.status !== undefined && data.status !== _cur.status) {
      const _allowed: Record<string, string[]> = { approved: ['reimbursed'], draft: ['submitted'], refused: [], reimbursed: [], submitted: ['approved', 'refused'] }
      if (!(_allowed[_cur.status] ?? []).includes(data.status)) {
        throw new Error(`Transition interdite : ${_cur.status} → ${data.status}`)
      }
    }
    const result = await prisma.expenseReport.update({
      where: { id, userId },
      data: { ...data }
    })
    return _serialize(result)
  },

  delete: async (userId: string, id: string): Promise<void> => {
    await prisma.expenseReport.delete({ where: { id, userId } })
  },

  transitionTo: async (userId: string, id: string, newStatus: string, data: Partial<UpdateExpenseReportInput> = {}): Promise<SerializedExpenseReport> => {
    const _cur = await prisma.expenseReport.findFirst({ where: { id, userId }, select: { status: true } })
    if (!_cur) notFound()
    const _allowed: Record<string, string[]> = { approved: ['reimbursed'], draft: ['submitted'], refused: [], reimbursed: [], submitted: ['approved', 'refused'] }
    if (!(_allowed[_cur.status] ?? []).includes(newStatus)) {
      throw new Error(`Transition interdite : ${_cur.status} → ${newStatus}`)
    }
    // Seuls les champs déclarés pour l'état CIBLE sont écrits — jamais un champ
    // métier arbitraire (sinon transitionTo rouvrirait le verrou d'édition).
    const _fieldsByState: Record<string, string[]> = { refused: ['rejectionReason'] }
    const _keep = new Set(_fieldsByState[newStatus] ?? [])
    const _payload: Partial<UpdateExpenseReportInput> = {}
    for (const _k of Object.keys(data)) {
      if (_keep.has(_k) && (data as Record<string, unknown>)[_k] !== undefined) {
        (_payload as Record<string, unknown>)[_k] = (data as Record<string, unknown>)[_k]
      }
    }
    const result = await prisma.expenseReport.update({ where: { id, userId }, data: { ..._payload, status: newStatus as ExpenseReport['status'] } })
    return _serialize(result)
  },
}
