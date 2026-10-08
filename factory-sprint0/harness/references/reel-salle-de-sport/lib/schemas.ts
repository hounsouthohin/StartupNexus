// AUTO-GÉNÉRÉ PAR dev_zod_generator.py — NE PAS MODIFIER
// Schémas Zod alignés sur lib/types.ts et ProjectSpec.
// Utilisé dans les Server Actions pour valider les données entrantes.
import { z } from 'zod'

// ── Member ──────────────────────────────────────────────────
export const CreateMemberSchema = z.object({
  subscriptionId: z.string().min(1),
})

export const UpdateMemberSchema = z.object({
  subscriptionId: z.string().optional(),
})
export type CreateMemberInput = z.infer<typeof CreateMemberSchema>
export type UpdateMemberInput = z.infer<typeof UpdateMemberSchema>

// ── Subscription ──────────────────────────────────────────────────
export const CreateSubscriptionSchema = z.object({
  renewalDate: z.coerce.date(),
})

export const UpdateSubscriptionSchema = z.object({
  status: z.enum(["active", "inactive", "cancelled"]).optional(),
  renewalDate: z.coerce.date().optional(),
})
export type CreateSubscriptionInput = z.infer<typeof CreateSubscriptionSchema>
export type UpdateSubscriptionInput = z.infer<typeof UpdateSubscriptionSchema>

// ── Course ──────────────────────────────────────────────────
export const CreateCourseSchema = z.object({
  title: z.string().min(1),
  description: z.string().optional(),
  schedule: z.coerce.date(),
})

export const UpdateCourseSchema = z.object({
  title: z.string().optional(),
  description: z.string().optional(),
  schedule: z.coerce.date().optional(),
})
export type CreateCourseInput = z.infer<typeof CreateCourseSchema>
export type UpdateCourseInput = z.infer<typeof UpdateCourseSchema>

// ── Reservation ──────────────────────────────────────────────────
export const CreateReservationSchema = z.object({
  memberId: z.string().min(1),
})

export const UpdateReservationSchema = z.object({
  memberId: z.string().optional(),
})
export type CreateReservationInput = z.infer<typeof CreateReservationSchema>
export type UpdateReservationInput = z.infer<typeof UpdateReservationSchema>

// ── Payment ──────────────────────────────────────────────────
export const CreatePaymentSchema = z.object({
  amount: z.coerce.number().nonnegative(),
  date: z.coerce.date(),
})

export const UpdatePaymentSchema = z.object({
  amount: z.coerce.number().nonnegative().optional(),
  date: z.coerce.date().optional(),
})
export type CreatePaymentInput = z.infer<typeof CreatePaymentSchema>
export type UpdatePaymentInput = z.infer<typeof UpdatePaymentSchema>
