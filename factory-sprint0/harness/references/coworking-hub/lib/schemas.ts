// AUTO-GÉNÉRÉ PAR dev_zod_generator.py — NE PAS MODIFIER
// Schémas Zod alignés sur lib/types.ts et ProjectSpec.
// Utilisé dans les Server Actions pour valider les données entrantes.
import { z } from 'zod'

// ── Space ──────────────────────────────────────────────────
export const CreateSpaceSchema = z.object({
  name: z.string().min(1),
  description: z.string().min(1),
  type: z.enum(["private_office", "meeting_room", "flex_desk"]),
  capacity: z.coerce.number().int().nonnegative(),
  hourlyRate: z.coerce.number().nonnegative(),
  address: z.string().min(1),
})

export const UpdateSpaceSchema = z.object({
  name: z.string().optional(),
  description: z.string().optional(),
  type: z.enum(["private_office", "meeting_room", "flex_desk"]).optional(),
  capacity: z.coerce.number().int().nonnegative().optional(),
  hourlyRate: z.coerce.number().nonnegative().optional(),
  address: z.string().optional(),
})
export type CreateSpaceInput = z.infer<typeof CreateSpaceSchema>
export type UpdateSpaceInput = z.infer<typeof UpdateSpaceSchema>

// ── Member ──────────────────────────────────────────────────
export const CreateMemberSchema = z.object({
  name: z.string().min(1),
  email: z.string().email(),
  company: z.string().optional(),
  phone: z.string().optional(),
})

export const UpdateMemberSchema = z.object({
  name: z.string().optional(),
  email: z.string().email().optional(),
  company: z.string().optional(),
  phone: z.string().optional(),
})
export type CreateMemberInput = z.infer<typeof CreateMemberSchema>
export type UpdateMemberInput = z.infer<typeof UpdateMemberSchema>

// ── Reservation ──────────────────────────────────────────────────
export const CreateReservationSchema = z.object({
  date: z.coerce.date(),
  startTime: z.coerce.date(),
  endTime: z.coerce.date(),
  spaceId: z.string().min(1),
  memberId: z.string().min(1),
})

export const UpdateReservationSchema = z.object({
  date: z.coerce.date().optional(),
  startTime: z.coerce.date().optional(),
  endTime: z.coerce.date().optional(),
  status: z.enum(["requested", "confirmed", "refused", "completed", "cancelled"]).optional(),
  reason: z.string().optional(),
  spaceId: z.string().optional(),
  memberId: z.string().optional(),
})
export type CreateReservationInput = z.infer<typeof CreateReservationSchema>
export type UpdateReservationInput = z.infer<typeof UpdateReservationSchema>

// ── Invoice ──────────────────────────────────────────────────
export const CreateInvoiceSchema = z.object({
  amount: z.coerce.number().nonnegative(),
  issueDate: z.coerce.date(),
  reservationId: z.string().min(1),
})

export const UpdateInvoiceSchema = z.object({
  amount: z.coerce.number().nonnegative().optional(),
  issueDate: z.coerce.date().optional(),
  status: z.enum(["pending", "paid", "overdue"]).optional(),
  reservationId: z.string().optional(),
})
export type CreateInvoiceInput = z.infer<typeof CreateInvoiceSchema>
export type UpdateInvoiceInput = z.infer<typeof UpdateInvoiceSchema>
