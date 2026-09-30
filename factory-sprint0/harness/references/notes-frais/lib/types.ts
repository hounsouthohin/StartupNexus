// ── AUTO-GÉNÉRÉ PAR dev_types_generator.py — NE PAS MODIFIER ────────────────
// Source de vérité des types partagés entre tous les fichiers du projet.
// Regénéré à chaque run depuis ProjectSpec.
// ─────────────────────────────────────────────────────────────────────────────

import type { Prisma, ExpenseCategory, ExpenseStatus } from '@prisma/client'
export type { Prisma, ExpenseCategory, ExpenseStatus }
// Types Prisma — disponibles après `prisma generate`
export type { ExpenseReport } from '@prisma/client'

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

// Types d'entrée pour ExpenseReport
export type CreateExpenseReportInput = Omit<Prisma.ExpenseReportUncheckedCreateInput, 'createdAt' | 'id' | 'updatedAt' | 'userId'>
export type UpdateExpenseReportInput = Partial<CreateExpenseReportInput>

// ExpenseReport — retour service (DateTime → string, NE PAS appeler .toISOString())
export type SerializedExpenseReport = {
  id: string
  title: string
  amount: number
  expenseDate: string
  category: ExpenseCategory
  description: string | null
  status: ExpenseStatus
  rejectionReason: string | null
  createdAt: string
  updatedAt: string
}

// Paramètres de route pour les pages dynamiques
export type DynamicIdPageParams = { params: Promise<{ id: string }> }

// Types Clerk — userId garanti non-null dans les routes protégées
export type AuthenticatedRequest = Request & { auth: { userId: string } }
