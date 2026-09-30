// AUTO-GÉNÉRÉ PAR dev_service_generator.py — NE PAS MODIFIER
import { notFound } from 'next/navigation'
import prisma from '@/lib/prisma'
import type { Vehicle } from '@prisma/client'
import type { CreateVehicleInput, UpdateVehicleInput, SerializedVehicle } from '@/lib/types'

const _serialize = (item: Vehicle): SerializedVehicle => {
  const { userId: _owner, ...rest } = item
  return ({
    ...rest,
  createdAt: rest.createdAt.toISOString(),
  updatedAt: rest.updatedAt.toISOString(),
  }) as SerializedVehicle
}

export const vehicleService = {
  getAll: async (userId: string, page: number = 1, pageSize: number = 20): Promise<SerializedVehicle[]> => {
    const items = await prisma.vehicle.findMany({ where: { userId }, select: { id: true, brand: true, model: true, licensePlate: true, clientId: true, createdAt: true, updatedAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedVehicle[]
  },

  getById: async (userId: string, id: string): Promise<SerializedVehicle> => {
    const item = await prisma.vehicle.findFirst({ where: { id, userId } })
    if (!item) notFound()
    return _serialize(item)
  },

  create: async (userId: string, data: CreateVehicleInput): Promise<SerializedVehicle> => {
    if (data.clientId) {
      const _owned_clientId = await prisma.client.findFirst({ where: { id: data.clientId, userId: userId }, select: { id: true } })
      if (!_owned_clientId) throw new Error('Référence liée introuvable.')
    }
    const result = await prisma.vehicle.create({
      data: { ...data, userId }
    })
    return _serialize(result)
  },

  update: async (userId: string, id: string, data: UpdateVehicleInput): Promise<SerializedVehicle> => {
    if (data.clientId) {
      const _owned_clientId = await prisma.client.findFirst({ where: { id: data.clientId, userId: userId }, select: { id: true } })
      if (!_owned_clientId) throw new Error('Référence liée introuvable.')
    }
    const result = await prisma.vehicle.update({
      where: { id, userId },
      data: { ...data }
    })
    return _serialize(result)
  },

  delete: async (userId: string, id: string): Promise<void> => {
    await prisma.vehicle.delete({ where: { id, userId } })
  },

  getByClientId: async (userId: string, clientId: string, page: number = 1, pageSize: number = 20): Promise<SerializedVehicle[]> => {
    const items = await prisma.vehicle.findMany({ where: { clientId, userId: userId }, select: { id: true, brand: true, model: true, licensePlate: true, clientId: true, createdAt: true, updatedAt: true }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedVehicle[]
  },

  getAllWithRelations: async (userId: string, page: number = 1, pageSize: number = 20): Promise<SerializedVehicle[]> => {
    const items = await prisma.vehicle.findMany({ where: { userId }, select: { id: true, brand: true, model: true, licensePlate: true, clientId: true, createdAt: true, updatedAt: true, client: { select: { id: true, name: true, phone: true } }, repairs: { select: { id: true, description: true, status: true, reasonForRejection: true, amountCharged: true } } }, orderBy: { createdAt: 'desc' }, take: pageSize, skip: (page - 1) * pageSize })
    return items.map(item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() })) as SerializedVehicle[]
  },

  getByIdWithRelations: async (userId: string, id: string): Promise<SerializedVehicle> => {
    const item = await prisma.vehicle.findFirst({ where: { id, userId }, select: { id: true, brand: true, model: true, licensePlate: true, clientId: true, createdAt: true, updatedAt: true, client: { select: { id: true, name: true, phone: true } }, repairs: { select: { id: true, description: true, status: true, reasonForRejection: true, amountCharged: true } } } })
    if (!item) notFound()
    return (item => ({ ...item, createdAt: item.createdAt.toISOString(), updatedAt: item.updatedAt.toISOString() }))(item) as SerializedVehicle
  },
}
