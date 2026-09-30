// AUTO-GÉNÉRÉ PAR dev_zod_generator.py — NE PAS MODIFIER
// Schémas Zod alignés sur lib/types.ts et ProjectSpec.
// Utilisé dans les Server Actions pour valider les données entrantes.
import { z } from 'zod'

// ── Request ──────────────────────────────────────────────────
export const CreateRequestSchema = z.object({
  title: z.string().min(1),
  description: z.string().min(1),
  priority: z.enum(["low", "normal", "high"]),
})

export const UpdateRequestSchema = z.object({
  title: z.string().optional(),
  description: z.string().optional(),
  priority: z.enum(["low", "normal", "high"]).optional(),
  status: z.enum(["new", "in_progress", "resolved"]).optional(),
})
export type CreateRequestInput = z.infer<typeof CreateRequestSchema>
export type UpdateRequestInput = z.infer<typeof UpdateRequestSchema>
