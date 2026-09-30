// ── AUTO-GÉNÉRÉ PAR dev_types_generator.py — NE PAS MODIFIER ────────────────
// Source de vérité des types partagés entre tous les fichiers du projet.
// Regénéré à chaque run depuis ProjectSpec.
// ─────────────────────────────────────────────────────────────────────────────

import type { Prisma, SubscriptionStatus } from '@prisma/client'
export type { Prisma, SubscriptionStatus }
// Types Prisma — disponibles après `prisma generate`
export type { Subscription, Category } from '@prisma/client'

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

// Types d'entrée pour Subscription
export type CreateSubscriptionInput = Omit<Prisma.SubscriptionUncheckedCreateInput, 'createdAt' | 'id' | 'updatedAt' | 'userId'>
export type UpdateSubscriptionInput = Partial<CreateSubscriptionInput>

// Subscription — retour service (DateTime → string, NE PAS appeler .toISOString())
export type SerializedSubscription = {
  id: string
  name: string
  monthlyPrice: number
  nextBillingDate: string
  status: SubscriptionStatus
  categoryId: string
  category?: { id: string; name: string; description: string | null; createdAt: string; updatedAt: string }
  createdAt: string
  updatedAt: string
}

// Types d'entrée pour Category
export type CreateCategoryInput = Omit<Prisma.CategoryUncheckedCreateInput, 'createdAt' | 'id' | 'updatedAt' | 'userId'>
export type UpdateCategoryInput = Partial<CreateCategoryInput>

// Category — retour service (DateTime → string, NE PAS appeler .toISOString())
export type SerializedCategory = {
  id: string
  name: string
  description: string | null
  subscriptions?: { id: string; name: string; monthlyPrice: number; nextBillingDate: string; status: SubscriptionStatus; categoryId: string; createdAt: string; updatedAt: string }[]
  createdAt: string
  updatedAt: string
}

// Paramètres de route pour les pages dynamiques
export type SubscriptionIdPageParams = { params: Promise<{ id: string }> }
export type DynamicIdPageParams = { params: Promise<{ id: string }> }

// Types Clerk — userId garanti non-null dans les routes protégées
export type AuthenticatedRequest = Request & { auth: { userId: string } }
