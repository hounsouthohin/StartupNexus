// AUTO-GÉNÉRÉ PAR dev_zod_generator.py — NE PAS MODIFIER
// Schémas Zod alignés sur lib/types.ts et ProjectSpec.
// Utilisé dans les Server Actions pour valider les données entrantes.
import { z } from 'zod'

// ── RunEvent ──────────────────────────────────────────────────
export const CreateRunEventSchema = z.object({
  title: z.string().min(1),
  dateTime: z.coerce.date(),
  location: z.string().min(1),
  distance: z.coerce.number().nonnegative(),
  description: z.string().min(1),
})

export const UpdateRunEventSchema = z.object({
  title: z.string().optional(),
  dateTime: z.coerce.date().optional(),
  location: z.string().optional(),
  distance: z.coerce.number().nonnegative().optional(),
  description: z.string().optional(),
  status: z.enum(["ouverte", "complete", "annulee"]).optional(),
})
export type CreateRunEventInput = z.infer<typeof CreateRunEventSchema>
export type UpdateRunEventInput = z.infer<typeof UpdateRunEventSchema>

// ── Participant ──────────────────────────────────────────────────
export const CreateParticipantSchema = z.object({
  name: z.string().min(1),
  email: z.string().email(),
  runEventId: z.string().min(1),
})

export const UpdateParticipantSchema = z.object({
  name: z.string().optional(),
  email: z.string().email().optional(),
  runEventId: z.string().optional(),
})
export type CreateParticipantInput = z.infer<typeof CreateParticipantSchema>
export type UpdateParticipantInput = z.infer<typeof UpdateParticipantSchema>
