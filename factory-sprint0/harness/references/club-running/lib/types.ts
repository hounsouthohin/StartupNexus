// ── AUTO-GÉNÉRÉ PAR dev_types_generator.py — NE PAS MODIFIER ────────────────
// Source de vérité des types partagés entre tous les fichiers du projet.
// Regénéré à chaque run depuis ProjectSpec.
// ─────────────────────────────────────────────────────────────────────────────

import type { Prisma, RunEventStatus } from '@prisma/client'
export type { Prisma, RunEventStatus }
// Types Prisma — disponibles après `prisma generate`
export type { RunEvent, Participant } from '@prisma/client'

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

// Types d'entrée pour RunEvent
export type CreateRunEventInput = Omit<Prisma.RunEventUncheckedCreateInput, 'createdAt' | 'id' | 'updatedAt' | 'userId'>
export type UpdateRunEventInput = Partial<CreateRunEventInput>

// RunEvent — retour service (DateTime → string, NE PAS appeler .toISOString())
export type SerializedRunEvent = {
  id: string
  title: string
  dateTime: string
  location: string
  distance: number
  description: string
  status: RunEventStatus
  participants?: { id: string; name: string; email: string; runEventId: string; createdAt: string; updatedAt: string }[]
  createdAt: string
  updatedAt: string
}

// Types d'entrée pour Participant
export type CreateParticipantInput = Omit<Prisma.ParticipantUncheckedCreateInput, 'createdAt' | 'id' | 'updatedAt' | 'userId'>
export type UpdateParticipantInput = Partial<CreateParticipantInput>

// Participant — retour service (DateTime → string, NE PAS appeler .toISOString())
export type SerializedParticipant = {
  id: string
  name: string
  email: string
  runEventId: string
  runEvent?: { id: string; title: string; dateTime: string; location: string; distance: number; description: string; status: RunEventStatus; createdAt: string; updatedAt: string }
  createdAt: string
  updatedAt: string
}

// Paramètres de route pour les pages dynamiques
export type DynamicIdPageParams = { params: Promise<{ id: string }> }

// Types Clerk — userId garanti non-null dans les routes protégées
export type AuthenticatedRequest = Request & { auth: { userId: string } }
