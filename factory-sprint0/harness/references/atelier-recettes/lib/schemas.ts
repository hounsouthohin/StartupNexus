// AUTO-GÉNÉRÉ PAR dev_zod_generator.py — NE PAS MODIFIER
// Schémas Zod alignés sur lib/types.ts et ProjectSpec.
// Utilisé dans les Server Actions pour valider les données entrantes.
import { z } from 'zod'

// ── Recipe ──────────────────────────────────────────────────
export const CreateRecipeSchema = z.object({
  title: z.string().min(1),
  instructions: z.string().min(1),
  preparationTime: z.coerce.number().int().nonnegative(),
  difficulty: z.enum(["facile", "moyenne", "difficile"]),
  published: z.coerce.boolean().optional(),
  tagIds: z.array(z.string()).optional(),
})

export const UpdateRecipeSchema = z.object({
  title: z.string().optional(),
  instructions: z.string().optional(),
  preparationTime: z.coerce.number().int().nonnegative().optional(),
  difficulty: z.enum(["facile", "moyenne", "difficile"]).optional(),
  published: z.preprocess(v => v === 'true' || v === 'on', z.boolean()).optional(),
  tagIds: z.array(z.string()).optional(),
})
export type CreateRecipeInput = z.infer<typeof CreateRecipeSchema>
export type UpdateRecipeInput = z.infer<typeof UpdateRecipeSchema>

// ── Tag ──────────────────────────────────────────────────
export const CreateTagSchema = z.object({
  name: z.string().min(1),
  recipeIds: z.array(z.string()).optional(),
})

export const UpdateTagSchema = z.object({
  name: z.string().optional(),
  recipeIds: z.array(z.string()).optional(),
})
export type CreateTagInput = z.infer<typeof CreateTagSchema>
export type UpdateTagInput = z.infer<typeof UpdateTagSchema>
