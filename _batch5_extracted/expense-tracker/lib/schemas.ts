// AUTO-GÉNÉRÉ PAR dev_zod_generator.py — NE PAS MODIFIER
// Schémas Zod alignés sur lib/types.ts et ProjectSpec.
// Utilisé dans les Server Actions pour valider les données entrantes.
import { z } from 'zod'

// ── Expense ──────────────────────────────────────────────────
export const CreateExpenseSchema = z.object({
  amount: z.number(),
  description: z.string().optional(),
  categoryId: z.string(),
})

export const UpdateExpenseSchema = CreateExpenseSchema.partial()
export type CreateExpenseInput = z.infer<typeof CreateExpenseSchema>
export type UpdateExpenseInput = z.infer<typeof UpdateExpenseSchema>

// ── Category ──────────────────────────────────────────────────
export const CreateCategorySchema = z.object({
  name: z.string(),
})

export const UpdateCategorySchema = CreateCategorySchema.partial()
export type CreateCategoryInput = z.infer<typeof CreateCategorySchema>
export type UpdateCategoryInput = z.infer<typeof UpdateCategorySchema>
