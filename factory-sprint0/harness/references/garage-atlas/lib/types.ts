// ── AUTO-GÉNÉRÉ PAR dev_types_generator.py — NE PAS MODIFIER ────────────────
// Source de vérité des types partagés entre tous les fichiers du projet.
// Regénéré à chaque run depuis ProjectSpec.
// ─────────────────────────────────────────────────────────────────────────────

import type { Prisma, RepairStatus } from '@prisma/client'
export type { Prisma, RepairStatus }
// Types Prisma — disponibles après `prisma generate`
export type { Client, Vehicle, Repair } from '@prisma/client'

// Type de réponse API standard — utilise-le dans tous les route handlers
export type ApiResponse<T> = {
  data: T | null
  error: string | null
  success: boolean
}

// Type de réponse paginée
export type PaginatedResponse<T> = ApiResponse<T[]> & {
  total: number
  page: number
  pageSize: number
}

// Types d'entrée pour Client
export type CreateClientInput = Omit<Prisma.ClientUncheckedCreateInput, 'createdAt' | 'id' | 'updatedAt' | 'userId'>
export type UpdateClientInput = Partial<CreateClientInput>

// Client — retour service (DateTime → string, NE PAS appeler .toISOString())
export type SerializedClient = {
  id: string
  name: string
  phone: string
  vehicles?: { id: string; brand: string; model: string; licensePlate: string; clientId: string; createdAt: string; updatedAt: string }[]
  createdAt: string
  updatedAt: string
}

// Types d'entrée pour Vehicle
export type CreateVehicleInput = Omit<Prisma.VehicleUncheckedCreateInput, 'createdAt' | 'id' | 'updatedAt' | 'userId'>
export type UpdateVehicleInput = Partial<CreateVehicleInput>

// Vehicle — retour service (DateTime → string, NE PAS appeler .toISOString())
export type SerializedVehicle = {
  id: string
  brand: string
  model: string
  licensePlate: string
  clientId: string
  client?: { id: string; name: string; phone: string; createdAt: string; updatedAt: string }
  repairs?: { id: string; description: string; status: RepairStatus; reasonForRejection: string | null; amountCharged: number | null; vehicleId: string; createdAt: string; updatedAt: string }[]
  createdAt: string
  updatedAt: string
}

// Types d'entrée pour Repair
export type CreateRepairInput = Omit<Prisma.RepairUncheckedCreateInput, 'createdAt' | 'id' | 'updatedAt' | 'userId'>
export type UpdateRepairInput = Partial<CreateRepairInput>

// Repair — retour service (DateTime → string, NE PAS appeler .toISOString())
export type SerializedRepair = {
  id: string
  description: string
  status: RepairStatus
  reasonForRejection: string | null
  amountCharged: number | null
  vehicleId: string
  vehicle?: { id: string; brand: string; model: string; licensePlate: string; clientId: string; createdAt: string; updatedAt: string }
  createdAt: string
  updatedAt: string
}

// Paramètres de route pour les pages dynamiques
export type ClientIdPageParams = { params: Promise<{ id: string }> }
export type VehicleIdPageParams = { params: Promise<{ id: string }> }
export type RepairIdPageParams = { params: Promise<{ id: string }> }

// Types Clerk — userId garanti non-null dans les routes protégées
export type AuthenticatedRequest = Request & { auth: { userId: string } }
