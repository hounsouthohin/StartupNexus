// ── AUTO-GÉNÉRÉ PAR dev_types_generator.py — NE PAS MODIFIER ────────────────
// Source de vérité des types partagés entre tous les fichiers du projet.
// Regénéré à chaque run depuis ProjectSpec.
// ─────────────────────────────────────────────────────────────────────────────

import type { Prisma } from '@prisma/client'
export type { Prisma }
// Types Prisma — disponibles après `prisma generate`
export type { LeaveRequest } from '@prisma/client'

export type { LeaveRequestStatus } from '@prisma/client'

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

// Types d'entrée pour LeaveRequest
export type CreateLeaveRequestInput = Omit<Prisma.LeaveRequestUncheckedCreateInput, 'createdAt' | 'id' | 'userId'>
export type UpdateLeaveRequestInput = Partial<CreateLeaveRequestInput>

// LeaveRequest — retour service (DateTime → string, NE PAS appeler .toISOString())
export type SerializedLeaveRequest = {
  id: string
  startDate: string
  endDate: string
  reason: string | null
  type: string
  status: "pending" | "approved" | "rejected"
  createdAt: string
}

// Paramètres de route pour les pages dynamiques
export type DynamicIdPageParams = { params: { id: string } }

// Types Clerk — userId garanti non-null dans les routes protégées
export type AuthenticatedRequest = Request & { auth: { userId: string } }
