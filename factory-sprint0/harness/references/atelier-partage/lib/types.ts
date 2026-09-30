// ── AUTO-GÉNÉRÉ PAR dev_types_generator.py — NE PAS MODIFIER ────────────────
// Source de vérité des types partagés entre tous les fichiers du projet.
// Regénéré à chaque run depuis ProjectSpec.
// ─────────────────────────────────────────────────────────────────────────────

import type { Prisma, ReservationStatus } from '@prisma/client'
export type { Prisma, ReservationStatus }
// Types Prisma — disponibles après `prisma generate`
export type { Workshop, Domain, Slot, Reservation } from '@prisma/client'

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

// Types d'entrée pour Workshop
export type CreateWorkshopInput = Omit<Prisma.WorkshopUncheckedCreateInput, 'createdAt' | 'domains' | 'id' | 'updatedAt' | 'userId'> & { domainIds?: string[] }
export type UpdateWorkshopInput = Partial<CreateWorkshopInput>

// Workshop — retour service (DateTime → string, NE PAS appeler .toISOString())
export type SerializedWorkshop = {
  id: string
  title: string
  description: string
  duration: number
  price: number
  domains?: { id: string; name: string; createdAt: string; updatedAt: string }[]
  slots?: { id: string; startTime: string; endTime: string; createdAt: string; updatedAt: string }[]
  createdAt: string
  updatedAt: string
}

// Types d'entrée pour Domain
export type CreateDomainInput = Omit<Prisma.DomainUncheckedCreateInput, 'createdAt' | 'id' | 'updatedAt' | 'userId' | 'workshops'> & { workshopIds?: string[] }
export type UpdateDomainInput = Partial<CreateDomainInput>

// Domain — retour service (DateTime → string, NE PAS appeler .toISOString())
export type SerializedDomain = {
  id: string
  name: string
  workshops?: { id: string; title: string; description: string; duration: number; price: number; createdAt: string; updatedAt: string }[]
  createdAt: string
  updatedAt: string
}

// Types d'entrée pour Slot
export type CreateSlotInput = Omit<Prisma.SlotUncheckedCreateInput, 'createdAt' | 'id' | 'updatedAt' | 'workshopId'>
export type UpdateSlotInput = Partial<CreateSlotInput>

// Slot — retour service (DateTime → string, NE PAS appeler .toISOString())
export type SerializedSlot = {
  id: string
  startTime: string
  endTime: string
  workshop?: { id: string; title: string; description: string; duration: number; price: number; createdAt: string; updatedAt: string }
  reservations?: { id: string; status: ReservationStatus; reason: string | null; slotId: string; createdAt: string; updatedAt: string }[]
  createdAt: string
  updatedAt: string
}

// Types d'entrée pour Reservation
export type CreateReservationInput = Omit<Prisma.ReservationUncheckedCreateInput, 'createdAt' | 'id' | 'updatedAt' | 'userId'>
export type UpdateReservationInput = Partial<CreateReservationInput>

// Reservation — retour service (DateTime → string, NE PAS appeler .toISOString())
export type SerializedReservation = {
  id: string
  status: ReservationStatus
  reason: string | null
  slotId: string
  slot?: { id: string; startTime: string; endTime: string; createdAt: string; updatedAt: string }
  createdAt: string
  updatedAt: string
}

// Paramètres de route pour les pages dynamiques
export type WorkshopIdPageParams = { params: Promise<{ id: string }> }
export type ReservationIdPageParams = { params: Promise<{ id: string }> }

// Types Clerk — userId garanti non-null dans les routes protégées
export type AuthenticatedRequest = Request & { auth: { userId: string } }
