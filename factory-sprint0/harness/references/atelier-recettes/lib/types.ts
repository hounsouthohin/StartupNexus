// ── AUTO-GÉNÉRÉ PAR dev_types_generator.py — NE PAS MODIFIER ────────────────
// Source de vérité des types partagés entre tous les fichiers du projet.
// Regénéré à chaque run depuis ProjectSpec.
// ─────────────────────────────────────────────────────────────────────────────

import type { Prisma, Difficulty } from '@prisma/client'
export type { Prisma, Difficulty }
// Types Prisma — disponibles après `prisma generate`
export type { Recipe, Tag } from '@prisma/client'

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

// Types d'entrée pour Recipe
export type CreateRecipeInput = Omit<Prisma.RecipeUncheckedCreateInput, 'createdAt' | 'id' | 'slug' | 'tags' | 'updatedAt' | 'userId'> & { tagIds?: string[] }
export type UpdateRecipeInput = Partial<CreateRecipeInput>

// Recipe — retour service (DateTime → string, NE PAS appeler .toISOString())
export type SerializedRecipe = {
  id: string
  title: string
  instructions: string
  preparationTime: number
  difficulty: Difficulty
  published: boolean
  slug: string
  tags?: { id: string; name: string; createdAt: string; updatedAt: string }[]
  createdAt: string
  updatedAt: string
}

// Types d'entrée pour Tag
export type CreateTagInput = Omit<Prisma.TagUncheckedCreateInput, 'createdAt' | 'id' | 'recipes' | 'updatedAt' | 'userId'> & { recipeIds?: string[] }
export type UpdateTagInput = Partial<CreateTagInput>

// Tag — retour service (DateTime → string, NE PAS appeler .toISOString())
export type SerializedTag = {
  id: string
  name: string
  recipes?: { id: string; title: string; instructions: string; preparationTime: number; difficulty: Difficulty; published: boolean; slug: string; createdAt: string; updatedAt: string }[]
  createdAt: string
  updatedAt: string
}

// Paramètres de route pour les pages dynamiques
export type RecipeSlugPageParams = { params: Promise<{ slug: string }> }
export type TagIdPageParams = { params: Promise<{ id: string }> }

// Types Clerk — userId garanti non-null dans les routes protégées
export type AuthenticatedRequest = Request & { auth: { userId: string } }
