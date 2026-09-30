// ── AUTO-GÉNÉRÉ PAR dev_types_generator.py — NE PAS MODIFIER ────────────────
// Source de vérité des types partagés entre tous les fichiers du projet.
// Regénéré à chaque run depuis ProjectSpec.
// ─────────────────────────────────────────────────────────────────────────────

import type { Prisma, RequestPriority, RequestStatus } from '@prisma/client'
export type { Prisma, RequestPriority, RequestStatus }
// Types Prisma — disponibles après `prisma generate`
export type { Request } from '@prisma/client'

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

// Types d'entrée pour Request
export type CreateRequestInput = Omit<Prisma.RequestUncheckedCreateInput, 'createdAt' | 'id' | 'updatedAt' | 'userId'>
export type UpdateRequestInput = Partial<CreateRequestInput>

// Request — retour service (DateTime → string, NE PAS appeler .toISOString())
export type SerializedRequest = {
  id: string
  title: string
  description: string
  priority: RequestPriority
  status: RequestStatus
  createdAt: string
  updatedAt: string
}

// Paramètres de route pour les pages dynamiques
export type RequestIdPageParams = { params: Promise<{ id: string }> }

// Types Clerk — userId garanti non-null dans les routes protégées
export type AuthenticatedRequest = Request & { auth: { userId: string } }
