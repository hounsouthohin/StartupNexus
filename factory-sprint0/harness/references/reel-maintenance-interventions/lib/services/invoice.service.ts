// AUTO-GÉNÉRÉ PAR dev_service_generator.py — NE PAS MODIFIER
import { notFound } from 'next/navigation'
import prisma from '@/lib/prisma'
import type { Invoice } from '@prisma/client'
import type { CreateInvoiceInput, UpdateInvoiceInput, SerializedInvoice } from '@/lib/types'

const _serialize = (item: Invoice): SerializedInvoice => {
  const { userId: _owner, ...rest } = item
  return ({
    ...rest,
  date: rest.date.toISOString(),
  createdAt: rest.createdAt.toISOString(),
  updatedAt: rest.updatedAt.toISOString(),
  }) as SerializedInvoice
}

export const invoiceService = {
  getAll: async (userId: string, page: number = 1, pageSize: number = 20): Promise<SerializedInvoice[]> => {
    const items = await prisma.invoice.findMany({ where: { userId }, select: { id: true, number: true, date: true, pdfUrl: true, clientId: true, technicianId: true, createdAt: true, updatedAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, date: item.date.toISOString(), createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedInvoice[]
  },

  getAllAsAdmin: async (page: number = 1, pageSize: number = 20): Promise<SerializedInvoice[]> => {
    const items = await prisma.invoice.findMany({ select: { id: true, number: true, date: true, pdfUrl: true, clientId: true, technicianId: true, createdAt: true, updatedAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, date: item.date.toISOString(), createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedInvoice[]
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
    if (data.clientId) {
      const _owned_clientId = await prisma.client.findFirst({ where: { id: data.clientId, userId: userId }, select: { id: true } })
      if (!_owned_clientId) throw new Error('Référence liée introuvable.')
    }
    if (data.technicianId) {
      const _owned_technicianId = await prisma.technician.findFirst({ where: { id: data.technicianId, userId: userId }, select: { id: true } })
      if (!_owned_technicianId) throw new Error('Référence liée introuvable.')
    }
    const result = await prisma.invoice.create({
      data: { ...data, userId }
    })
    return _serialize(result)
  },

  update: async (userId: string, id: string, data: UpdateInvoiceInput): Promise<SerializedInvoice> => {
    if (data.clientId) {
      const _owned_clientId = await prisma.client.findFirst({ where: { id: data.clientId, userId: userId }, select: { id: true } })
      if (!_owned_clientId) throw new Error('Référence liée introuvable.')
    }
    if (data.technicianId) {
      const _owned_technicianId = await prisma.technician.findFirst({ where: { id: data.technicianId, userId: userId }, select: { id: true } })
      if (!_owned_technicianId) throw new Error('Référence liée introuvable.')
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

  getByClientId: async (userId: string, clientId: string, page: number = 1, pageSize: number = 20): Promise<SerializedInvoice[]> => {
    const items = await prisma.invoice.findMany({ where: { clientId, userId: userId }, select: { id: true, number: true, date: true, pdfUrl: true, clientId: true, technicianId: true, createdAt: true, updatedAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, date: item.date.toISOString(), createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedInvoice[]
  },

  getByTechnicianId: async (userId: string, technicianId: string, page: number = 1, pageSize: number = 20): Promise<SerializedInvoice[]> => {
    const items = await prisma.invoice.findMany({ where: { technicianId, userId: userId }, select: { id: true, number: true, date: true, pdfUrl: true, clientId: true, technicianId: true, createdAt: true, updatedAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, date: item.date.toISOString(), createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedInvoice[]
  },

  getAllWithRelations: async (userId: string, page: number = 1, pageSize: number = 20): Promise<SerializedInvoice[]> => {
    const items = await prisma.invoice.findMany({ where: { userId }, select: { id: true, number: true, date: true, pdfUrl: true, clientId: true, technicianId: true, createdAt: true, updatedAt: true, client: { select: { id: true, name: true, email: true, phone: true, address: true } }, technician: { select: { id: true, name: true, email: true, phone: true, region: true } } }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, date: item.date.toISOString(), createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedInvoice[]
  },

  getByIdWithRelations: async (userId: string, id: string): Promise<SerializedInvoice> => {
    const item = await prisma.invoice.findFirst({ where: { id, userId }, select: { id: true, number: true, date: true, pdfUrl: true, clientId: true, technicianId: true, createdAt: true, updatedAt: true, client: { select: { id: true, name: true, email: true, phone: true, address: true } }, technician: { select: { id: true, name: true, email: true, phone: true, region: true } } } })
    if (!item) notFound()
    return (item => ({ ...item, date: item.date.toISOString(), createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() }))(item) as SerializedInvoice
  },

  getByIdWithRelationsAsAdmin: async (id: string): Promise<SerializedInvoice> => {
    const item = await prisma.invoice.findFirst({ where: { id }, select: { id: true, number: true, date: true, pdfUrl: true, clientId: true, technicianId: true, createdAt: true, updatedAt: true, client: { select: { id: true, name: true, email: true, phone: true, address: true } }, technician: { select: { id: true, name: true, email: true, phone: true, region: true } } } })
    if (!item) notFound()
    return (item => ({ ...item, date: item.date.toISOString(), createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() }))(item) as SerializedInvoice
  },
}
