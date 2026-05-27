// ── AUTO-GÉNÉRÉ PAR dev_types_generator.py — NE PAS MODIFIER ────────────────
// Source de vérité des types partagés entre tous les fichiers du projet.
// Regénéré à chaque run depuis ProjectSpec.
// ─────────────────────────────────────────────────────────────────────────────

import type { Prisma } from '@prisma/client'
export type { Prisma }
// Types Prisma — disponibles après `prisma generate`
export type { Category, Article } from '@prisma/client'

export type { ArticleStatus } from '@prisma/client'

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
  articles?: { id: string; title: string; content: string; slug: string; status: "draft" | "published" | "archived"; categoryId: string; authorId: string; createdAt: string }[]
  createdAt: string
}

// Types d'entrée pour Article
export type CreateArticleInput = Omit<Prisma.ArticleUncheckedCreateInput, 'authorId' | 'createdAt' | 'id'>
export type UpdateArticleInput = Partial<CreateArticleInput>

// Article — retour service (DateTime → string, NE PAS appeler .toISOString())
export type SerializedArticle = {
  id: string
  title: string
  content: string
  slug: string
  status: "draft" | "published" | "archived"
  categoryId: string
  category?: { id: string; name: string; userId: string; createdAt: string }
  createdAt: string
}

// Paramètres de route pour les pages dynamiques
export type ArticleSlugPageParams = { params: { slug: string } }

// Types Clerk — userId garanti non-null dans les routes protégées
export type AuthenticatedRequest = Request & { auth: { userId: string } }
