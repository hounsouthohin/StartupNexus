// AUTO-GÉNÉRÉ PAR dev_zod_generator.py — NE PAS MODIFIER
// Schémas Zod alignés sur lib/types.ts et ProjectSpec.
// Utilisé dans les Server Actions pour valider les données entrantes.
import { z } from 'zod'

// ── Subscription ──────────────────────────────────────────────────
export const CreateSubscriptionSchema = z.object({
  name: z.string().min(1),
  monthlyPrice: z.coerce.number().nonnegative(),
  nextBillingDate: z.coerce.date(),
  categoryId: z.string().min(1),
})

export const UpdateSubscriptionSchema = z.object({
  name: z.string().optional(),
  monthlyPrice: z.coerce.number().nonnegative().optional(),
  nextBillingDate: z.coerce.date().optional(),
  status: z.enum(["active", "paused", "cancelled"]).optional(),
  categoryId: z.string().optional(),
})
export type CreateSubscriptionInput = z.infer<typeof CreateSubscriptionSchema>
export type UpdateSubscriptionInput = z.infer<typeof UpdateSubscriptionSchema>

// ── Category ──────────────────────────────────────────────────
export const CreateCategorySchema = z.object({
  name: z.string().min(1),
  description: z.string().optional(),
})

export const UpdateCategorySchema = z.object({
  name: z.string().optional(),
  description: z.string().optional(),
})
export type CreateCategoryInput = z.infer<typeof CreateCategorySchema>
export type UpdateCategoryInput = z.infer<typeof UpdateCategorySchema>
