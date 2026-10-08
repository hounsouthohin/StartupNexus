// ── AUTO-GÉNÉRÉ PAR dev_types_generator.py — NE PAS MODIFIER ────────────────
// Source de vérité des types partagés entre tous les fichiers du projet.
// Regénéré à chaque run depuis ProjectSpec.
// ─────────────────────────────────────────────────────────────────────────────

import type { Prisma, ReservationStatus } from '@prisma/client'
export type { Prisma, ReservationStatus }
// Types Prisma — disponibles après `prisma generate`
export type { Reservation, Client, Provider, Manager, Alert } from '@prisma/client'

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

// Types d'entrée pour Reservation
export type CreateReservationInput = Omit<Prisma.ReservationUncheckedCreateInput, 'clientId' | 'createdAt' | 'id' | 'updatedAt'>
export type UpdateReservationInput = Partial<CreateReservationInput>

// Reservation — retour service (DateTime → string, NE PAS appeler .toISOString())
export type SerializedReservation = {
  id: string
  date: string
  status: ReservationStatus
  client?: { id: string; name: string; email: string; createdAt: string; updatedAt: string }
  providerId: string
  provider?: { id: string; name: string; email: string; createdAt: string; updatedAt: string }
  managerId: string | null
  manager?: { id: string; name: string; email: string; createdAt: string; updatedAt: string }
  createdAt: string
  updatedAt: string
}

// Types d'entrée pour Client
export type CreateClientInput = Omit<Prisma.ClientUncheckedCreateInput, 'createdAt' | 'id' | 'providerId' | 'updatedAt'>
export type UpdateClientInput = Partial<CreateClientInput>

// Client — retour service (DateTime → string, NE PAS appeler .toISOString())
export type SerializedClient = {
  id: string
  name: string
  email: string
  provider?: { id: string; name: string; email: string; createdAt: string; updatedAt: string }
  createdAt: string
  updatedAt: string
}

// Types d'entrée pour Provider
export type CreateProviderInput = Omit<Prisma.ProviderUncheckedCreateInput, 'createdAt' | 'id' | 'managers' | 'updatedAt' | 'userId'> & { managerIds?: string[] }
export type UpdateProviderInput = Partial<CreateProviderInput>

// Provider — retour service (DateTime → string, NE PAS appeler .toISOString())
export type SerializedProvider = {
  id: string
  name: string
  email: string
  managers?: { id: string; name: string; email: string; createdAt: string; updatedAt: string }[]
  clients?: { id: string; name: string; email: string; createdAt: string; updatedAt: string }[]
  reservations?: { id: string; date: string; status: ReservationStatus; providerId: string; managerId: string | null; createdAt: string; updatedAt: string }[]
  createdAt: string
  updatedAt: string
}

// Types d'entrée pour Manager
export type CreateManagerInput = Omit<Prisma.ManagerUncheckedCreateInput, 'createdAt' | 'id' | 'providers' | 'updatedAt' | 'userId'> & { providerIds?: string[] }
export type UpdateManagerInput = Partial<CreateManagerInput>

// Manager — retour service (DateTime → string, NE PAS appeler .toISOString())
export type SerializedManager = {
  id: string
  name: string
  email: string
  providers?: { id: string; name: string; email: string; createdAt: string; updatedAt: string }[]
  reservations?: { id: string; date: string; status: ReservationStatus; providerId: string; managerId: string | null; createdAt: string; updatedAt: string }[]
  createdAt: string
  updatedAt: string
}

// Types d'entrée pour Alert
export type CreateAlertInput = Omit<Prisma.AlertUncheckedCreateInput, 'createdAt' | 'id' | 'updatedAt' | 'userId'>
export type UpdateAlertInput = Partial<CreateAlertInput>

// Alert — retour service (DateTime → string, NE PAS appeler .toISOString())
export type SerializedAlert = {
  id: string
  message: string
  reservationId: string
  reservation?: { id: string; date: string; status: ReservationStatus; providerId: string; managerId: string | null; createdAt: string; updatedAt: string }
  createdAt: string
  updatedAt: string
}

// Paramètres de route pour les pages dynamiques
export type ReservationIdPageParams = { params: Promise<{ id: string }> }
export type ClientIdPageParams = { params: Promise<{ id: string }> }
export type ProviderIdPageParams = { params: Promise<{ id: string }> }
export type ManagerIdPageParams = { params: Promise<{ id: string }> }
export type AlertIdPageParams = { params: Promise<{ id: string }> }

// Types Clerk — userId garanti non-null dans les routes protégées
export type AuthenticatedRequest = Request & { auth: { userId: string } }
