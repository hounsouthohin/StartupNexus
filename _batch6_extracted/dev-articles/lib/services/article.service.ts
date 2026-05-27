// AUTO-GÉNÉRÉ PAR dev_service_generator.py — NE PAS MODIFIER
import { notFound } from 'next/navigation'
import prisma from '@/lib/prisma'
import type { Article } from '@prisma/client'
import type { CreateArticleInput, UpdateArticleInput, SerializedArticle } from '@/lib/types'

const _serialize = (item: Article): SerializedArticle => {
  const { authorId: _owner, ...rest } = item
  return ({
    ...rest,
  createdAt: rest.createdAt.toISOString(),
  }) as SerializedArticle
}

export const articleService = {
  getAll: async (authorId: string, page: number = 1, pageSize: number = 20): Promise<SerializedArticle[]> => {
    const items = await prisma.article.findMany({ where: { authorId }, select: { id: true, title: true, content: true, slug: true, status: true, createdAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, createdAt: item.createdAt.toISOString() })) as SerializedArticle[]
  },

  getPublished: async (): Promise<SerializedArticle[]> => {
    const items = await prisma.article.findMany({ where: { status: 'published' }, select: { id: true, title: true, content: true, slug: true, status: true, createdAt: true }, orderBy: { createdAt: 'desc' }, take: 50, skip: 0 })
    return items.map(item => ({ ...item, createdAt: item.createdAt.toISOString() })) as SerializedArticle[]
  },

  getById: async (authorId: string, id: string): Promise<SerializedArticle> => {
    const item = await prisma.article.findFirst({ where: { id, authorId } })
    if (!item) notFound()
    return _serialize(item)
  },

  getPublicById: async (id: string): Promise<SerializedArticle> => {
    const item = await prisma.article.findUnique({ where: { id } })
    if (!item) notFound()
    return _serialize(item)
  },

  getPublicAll: async (): Promise<SerializedArticle[]> => {
    const items = await prisma.article.findMany({ where: { status: 'published' }, select: { id: true, title: true, content: true, slug: true, status: true, createdAt: true }, orderBy: { createdAt: 'desc' }, take: 50, skip: 0 })
    return items.map(item => ({ ...item, createdAt: item.createdAt.toISOString() })) as SerializedArticle[]
  },

  getBySlug: async (slug: string): Promise<SerializedArticle> => {
    const item = await prisma.article.findUnique({ where: { slug } })
    if (!item) notFound()
    return _serialize(item)
  },

  create: async (authorId: string, data: CreateArticleInput): Promise<Article> => {
    return prisma.article.create({
      data: { ...data, authorId }
    })
  },

  update: async (authorId: string, id: string, data: UpdateArticleInput): Promise<Article> => {
    return prisma.article.update({
      where: { id, authorId },
      data: { ...data }
    })
  },

  delete: async (authorId: string, id: string): Promise<void> => {
    await prisma.article.delete({ where: { id, authorId } })
  },
}
