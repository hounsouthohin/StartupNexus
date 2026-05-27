// AUTO-GÉNÉRÉ PAR dev_zod_generator.py — NE PAS MODIFIER
// Schémas Zod alignés sur lib/types.ts et ProjectSpec.
// Utilisé dans les Server Actions pour valider les données entrantes.
import { z } from 'zod'

// ── Recipe ──────────────────────────────────────────────────
export const CreateRecipeSchema = z.object({
  title: z.string(),
  description: z.string(),
  slug: z.string(),
  status: z.enum(["draft", "published", "archived"]).optional(),
})

export const UpdateRecipeSchema = CreateRecipeSchema.partial()
export type CreateRecipeInput = z.infer<typeof CreateRecipeSchema>
export type UpdateRecipeInput = z.infer<typeof UpdateRecipeSchema>

// ── Category ──────────────────────────────────────────────────
export const CreateCategorySchema = z.object({
  name: z.string(),
})

export const UpdateCategorySchema = CreateCategorySchema.partial()
export type CreateCategoryInput = z.infer<typeof CreateCategorySchema>
export type UpdateCategoryInput = z.infer<typeof UpdateCategorySchema>
