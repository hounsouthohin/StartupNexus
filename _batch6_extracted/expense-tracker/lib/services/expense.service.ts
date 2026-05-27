// AUTO-GÉNÉRÉ PAR dev_service_generator.py — NE PAS MODIFIER
import { notFound } from 'next/navigation'
import prisma from '@/lib/prisma'
import type { Expense } from '@prisma/client'
import type { CreateExpenseInput, UpdateExpenseInput, SerializedExpense } from '@/lib/types'

const _serialize = (item: Expense): SerializedExpense => {
  const { userId: _owner, ...rest } = item
  return ({
    ...rest,
  createdAt: rest.createdAt.toISOString(),
  }) as SerializedExpense
}

export const expenseService = {
  getAll: async (userId: string, page: number = 1, pageSize: number = 20): Promise<SerializedExpense[]> => {
    const items = await prisma.expense.findMany({ where: { userId }, select: { id: true, amount: true, description: true, categoryId: true, createdAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, createdAt: item.createdAt.toISOString() })) as SerializedExpense[]
  },

  getById: async (userId: string, id: string): Promise<SerializedExpense> => {
    const item = await prisma.expense.findFirst({ where: { id, userId } })
    if (!item) notFound()
    return _serialize(item)
  },

  getAllWithRelations: async (userId: string): Promise<SerializedExpense[]> => {
    const items = await prisma.expense.findMany({ where: { userId }, select: { id: true, amount: true, description: true, categoryId: true, createdAt: true, category: { select: { id: true, name: true } } }, orderBy: { createdAt: 'desc' }, take: 20, skip: 0 })
    return items.map(item => ({ ...item, createdAt: item.createdAt.toISOString() })) as SerializedExpense[]
  },

  getByIdWithRelations: async (userId: string, id: string): Promise<SerializedExpense> => {
    const item = await prisma.expense.findFirst({ where: { id, userId }, select: { id: true, amount: true, description: true, categoryId: true, createdAt: true, category: { select: { id: true, name: true } } } })
    if (!item) notFound()
    return (item => ({ ...item, createdAt: item.createdAt.toISOString() }))(item) as SerializedExpense
  },

  create: async (userId: string, data: CreateExpenseInput): Promise<Expense> => {
    return prisma.expense.create({
      data: { ...data, userId }
    })
  },

  update: async (userId: string, id: string, data: UpdateExpenseInput): Promise<Expense> => {
    return prisma.expense.update({
      where: { id, userId },
      data: { ...data }
    })
  },

  delete: async (userId: string, id: string): Promise<void> => {
    await prisma.expense.delete({ where: { id, userId } })
  },
}
