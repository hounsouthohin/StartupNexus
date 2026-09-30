// ── AUTO-GÉNÉRÉ PAR dev_types_generator.py — NE PAS MODIFIER ────────────────
// Source de vérité des types partagés entre tous les fichiers du projet.
// Regénéré à chaque run depuis ProjectSpec.
// ─────────────────────────────────────────────────────────────────────────────

import type { Prisma, SpaceType, ReservationStatus, InvoiceStatus } from '@prisma/client'
export type { Prisma, SpaceType, ReservationStatus, InvoiceStatus }
// Types Prisma — disponibles après `prisma generate`
export type { Space, Member, Reservation, Invoice } from '@prisma/client'

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

// Types d'entrée pour Space
export type CreateSpaceInput = Omit<Prisma.SpaceUncheckedCreateInput, 'createdAt' | 'id' | 'updatedAt' | 'userId'>
export type UpdateSpaceInput = Partial<CreateSpaceInput>

// Space — retour service (DateTime → string, NE PAS appeler .toISOString())
export type SerializedSpace = {
  id: string
  name: string
  description: string
  type: SpaceType
  capacity: number
  hourlyRate: number
  address: string
  createdAt: string
  updatedAt: string
}

// Types d'entrée pour Member
export type CreateMemberInput = Omit<Prisma.MemberUncheckedCreateInput, 'createdAt' | 'id' | 'updatedAt' | 'userId'>
export type UpdateMemberInput = Partial<CreateMemberInput>

// Member — retour service (DateTime → string, NE PAS appeler .toISOString())
export type SerializedMember = {
  id: string
  name: string
  email: string
  company: string | null
  phone: string | null
  reservations?: { id: string; date: string; startTime: string; endTime: string; status: ReservationStatus; reason: string | null; spaceId: string; memberId: string; createdAt: string; updatedAt: string }[]
  invoices?: { id: string; amount: number; issueDate: string; status: InvoiceStatus; reservationId: string; createdAt: string; updatedAt: string }[]
  createdAt: string
  updatedAt: string
}

// Types d'entrée pour Reservation
export type CreateReservationInput = Omit<Prisma.ReservationUncheckedCreateInput, 'createdAt' | 'id' | 'updatedAt' | 'userId'>
export type UpdateReservationInput = Partial<CreateReservationInput>

// Reservation — retour service (DateTime → string, NE PAS appeler .toISOString())
export type SerializedReservation = {
  id: string
  date: string
  startTime: string
  endTime: string
  status: ReservationStatus
  reason: string | null
  spaceId: string
  space?: { id: string; name: string; description: string; type: SpaceType; capacity: number; hourlyRate: number; address: string; createdAt: string; updatedAt: string }
  memberId: string
  member?: { id: string; name: string; email: string; company: string | null; phone: string | null; createdAt: string; updatedAt: string }
  invoice?: { id: string; amount: number; issueDate: string; status: InvoiceStatus; reservationId: string; createdAt: string; updatedAt: string } | null
  createdAt: string
  updatedAt: string
}

// Types d'entrée pour Invoice
export type CreateInvoiceInput = Omit<Prisma.InvoiceUncheckedCreateInput, 'createdAt' | 'id' | 'updatedAt' | 'userId'>
export type UpdateInvoiceInput = Partial<CreateInvoiceInput>

// Invoice — retour service (DateTime → string, NE PAS appeler .toISOString())
export type SerializedInvoice = {
  id: string
  amount: number
  issueDate: string
  status: InvoiceStatus
  reservationId: string
  reservation?: { id: string; date: string; startTime: string; endTime: string; status: ReservationStatus; reason: string | null; spaceId: string; memberId: string; createdAt: string; updatedAt: string }
  createdAt: string
  updatedAt: string
}

// Paramètres de route pour les pages dynamiques
export type SpaceIdPageParams = { params: Promise<{ id: string }> }
export type ReservationIdPageParams = { params: Promise<{ id: string }> }
export type InvoiceIdPageParams = { params: Promise<{ id: string }> }

// Types Clerk — userId garanti non-null dans les routes protégées
export type AuthenticatedRequest = Request & { auth: { userId: string } }
