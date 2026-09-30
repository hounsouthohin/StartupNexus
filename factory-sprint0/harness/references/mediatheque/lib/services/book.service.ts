// AUTO-GÉNÉRÉ PAR dev_service_generator.py — NE PAS MODIFIER
import { notFound } from 'next/navigation'
import prisma from '@/lib/prisma'
import type { Book } from '@prisma/client'
import type { CreateBookInput, UpdateBookInput, SerializedBook } from '@/lib/types'

const _serialize = (item: Book): SerializedBook => {
  const rest = item
  return ({
    ...rest,
  createdAt: rest.createdAt.toISOString(),
  updatedAt: rest.updatedAt.toISOString(),
  }) as SerializedBook
}

export const bookService = {
  getAll: async (userId: string, page: number = 1, pageSize: number = 20): Promise<SerializedBook[]> => {
    const items = await prisma.book.findMany({ where: {  }, select: { id: true, title: true, author: true, summary: true, genre: true, publicationYear: true, createdAt: true, updatedAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedBook[]
  },

  getById: async (userId: string, id: string): Promise<SerializedBook> => {
    const item = await prisma.book.findFirst({ where: { id } })
    if (!item) notFound()
    return _serialize(item)
  },

  create: async (userId: string, data: CreateBookInput): Promise<SerializedBook> => {
    const result = await prisma.book.create({
      data: { ...data }
    })
    return _serialize(result)
  },

  update: async (userId: string, id: string, data: UpdateBookInput): Promise<SerializedBook> => {
    const result = await prisma.book.update({
      where: { id },
      data: { ...data }
    })
    return _serialize(result)
  },

  delete: async (userId: string, id: string): Promise<void> => {
    await prisma.book.delete({ where: { id } })
  },

  getPublicById: async (id: string): Promise<SerializedBook> => {
    const item = await prisma.book.findUnique({ where: { id } })
    if (!item) notFound()
    return _serialize(item)
  },

  getPublicAll: async (page: number = 1, pageSize: number = 20): Promise<SerializedBook[]> => {
    const items = await prisma.book.findMany({ select: { id: true, title: true, author: true, summary: true, genre: true, publicationYear: true, createdAt: true, updatedAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedBook[]
  },
}
