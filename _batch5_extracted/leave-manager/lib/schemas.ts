// AUTO-GÉNÉRÉ PAR dev_zod_generator.py — NE PAS MODIFIER
// Schémas Zod alignés sur lib/types.ts et ProjectSpec.
// Utilisé dans les Server Actions pour valider les données entrantes.
import { z } from 'zod'

// ── LeaveRequest ──────────────────────────────────────────────────
export const CreateLeaveRequestSchema = z.object({
  startDate: z.coerce.date(),
  endDate: z.coerce.date(),
  reason: z.string().optional(),
  type: z.string(),
  status: z.enum(["pending", "approved", "rejected"]).optional(),
})

export const UpdateLeaveRequestSchema = CreateLeaveRequestSchema.partial()
export type CreateLeaveRequestInput = z.infer<typeof CreateLeaveRequestSchema>
export type UpdateLeaveRequestInput = z.infer<typeof UpdateLeaveRequestSchema>
