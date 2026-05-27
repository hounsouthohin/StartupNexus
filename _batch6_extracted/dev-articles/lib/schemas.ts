// AUTO-GÉNÉRÉ PAR dev_zod_generator.py — NE PAS MODIFIER
// Schémas Zod alignés sur lib/types.ts et ProjectSpec.
// Utilisé dans les Server Actions pour valider les données entrantes.
import { z } from 'zod'

// ── Article ──────────────────────────────────────────────────
export const CreateArticleSchema = z.object({
  title: z.string(),
  content: z.string(),
  slug: z.string(),
  status: z.enum(["draft", "published", "archived"]).optional(),
})

export const UpdateArticleSchema = CreateArticleSchema.partial()
export type CreateArticleInput = z.infer<typeof CreateArticleSchema>
export type UpdateArticleInput = z.infer<typeof UpdateArticleSchema>

// ── Category ──────────────────────────────────────────────────
export const CreateCategorySchema = z.object({
  name: z.string(),
})

export const UpdateCategorySchema = CreateCategorySchema.partial()
export type CreateCategoryInput = z.infer<typeof CreateCategorySchema>
export type UpdateCategoryInput = z.infer<typeof UpdateCategorySchema>
