// ── AUTO-GÉNÉRÉ PAR dev_types_generator.py — NE PAS MODIFIER ────────────────
// Source de vérité des types partagés entre tous les fichiers du projet.
// Regénéré à chaque run depuis ProjectSpec.
// ─────────────────────────────────────────────────────────────────────────────

import type { Prisma } from '@prisma/client'
export type { Prisma }
// Types Prisma — disponibles après `prisma generate`
export type { Category, Expense } from '@prisma/client'

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

// Types d'entrée pour Category
export type CreateCategoryInput = Omit<Prisma.CategoryUncheckedCreateInput, 'createdAt' | 'id' | 'userId'>
export type UpdateCategoryInput = Partial<CreateCategoryInput>

// Category — retour service (DateTime → string, NE PAS appeler .toISOString())
export type SerializedCategory = {
  id: string
  name: string
  expenses?: { id: string; amount: number; description: string | null; categoryId: string; userId: string; createdAt: string }[]
  createdAt: string
}

// Types d'entrée pour Expense
export type CreateExpenseInput = Omit<Prisma.ExpenseUncheckedCreateInput, 'createdAt' | 'id' | 'userId'>
export type UpdateExpenseInput = Partial<CreateExpenseInput>

// Expense — retour service (DateTime → string, NE PAS appeler .toISOString())
export type SerializedExpense = {
  id: string
  amount: number
  description: string | null
  categoryId: string
  category?: { id: string; name: string; userId: string; createdAt: string }
  createdAt: string
}

// Paramètres de route pour les pages dynamiques
export type ExpenseIdPageParams = { params: { id: string } }

// Types Clerk — userId garanti non-null dans les routes protégées
export type AuthenticatedRequest = Request & { auth: { userId: string } }
