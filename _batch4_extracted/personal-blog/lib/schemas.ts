// AUTO-GÉNÉRÉ PAR dev_zod_generator.py — NE PAS MODIFIER
// Schémas Zod alignés sur lib/types.ts et ProjectSpec.
// Utilisé dans les Server Actions pour valider les données entrantes.
import { z } from 'zod'

// ── Category ──────────────────────────────────────────────────
export const CreateCategorySchema = z.object({
  name: z.string(),
})

export const UpdateCategorySchema = CreateCategorySchema.partial()
export type CreateCategoryInput = z.infer<typeof CreateCategorySchema>
export type UpdateCategoryInput = z.infer<typeof UpdateCategorySchema>

// ── Post ──────────────────────────────────────────────────
export const CreatePostSchema = z.object({
  title: z.string(),
  excerpt: z.string(),
  status: z.enum(["draft", "published"]).optional(),
  categoryId: z.string(),
})

export const UpdatePostSchema = CreatePostSchema.partial()
export type CreatePostInput = z.infer<typeof CreatePostSchema>
export type UpdatePostInput = z.infer<typeof UpdatePostSchema>
