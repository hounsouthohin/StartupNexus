// AUTO-GÉNÉRÉ PAR dev_zod_generator.py — NE PAS MODIFIER
// Schémas Zod alignés sur lib/types.ts et ProjectSpec.
// Utilisé dans les Server Actions pour valider les données entrantes.
import { z } from 'zod'

// ── Reservation ──────────────────────────────────────────────────
export const CreateReservationSchema = z.object({
  date: z.coerce.date(),
  providerId: z.string().min(1),
  managerId: z.string().min(1),
})

export const UpdateReservationSchema = z.object({
  date: z.coerce.date().optional(),
  status: z.enum(["pending", "confirmed", "cancelled"]).optional(),
  providerId: z.string().optional(),
  managerId: z.string().optional(),
})
export type CreateReservationInput = z.infer<typeof CreateReservationSchema>
export type UpdateReservationInput = z.infer<typeof UpdateReservationSchema>

// ── Client ──────────────────────────────────────────────────
export const CreateClientSchema = z.object({
  name: z.string().min(1),
  email: z.string().email(),
})

export const UpdateClientSchema = z.object({
  name: z.string().optional(),
  email: z.string().email().optional(),
})
export type CreateClientInput = z.infer<typeof CreateClientSchema>
export type UpdateClientInput = z.infer<typeof UpdateClientSchema>

// ── Provider ──────────────────────────────────────────────────
export const CreateProviderSchema = z.object({
  name: z.string().min(1),
  email: z.string().email(),
  managerIds: z.array(z.string()).optional(),
})

export const UpdateProviderSchema = z.object({
  name: z.string().optional(),
  email: z.string().email().optional(),
  managerIds: z.array(z.string()).optional(),
})
export type CreateProviderInput = z.infer<typeof CreateProviderSchema>
export type UpdateProviderInput = z.infer<typeof UpdateProviderSchema>

// ── Manager ──────────────────────────────────────────────────
export const CreateManagerSchema = z.object({
  name: z.string().min(1),
  email: z.string().email(),
  providerIds: z.array(z.string()).optional(),
})

export const UpdateManagerSchema = z.object({
  name: z.string().optional(),
  email: z.string().email().optional(),
  providerIds: z.array(z.string()).optional(),
})
export type CreateManagerInput = z.infer<typeof CreateManagerSchema>
export type UpdateManagerInput = z.infer<typeof UpdateManagerSchema>

// ── Alert ──────────────────────────────────────────────────
export const CreateAlertSchema = z.object({
  message: z.string().min(1),
  reservationId: z.string().min(1),
})

export const UpdateAlertSchema = z.object({
  message: z.string().optional(),
  reservationId: z.string().optional(),
})
export type CreateAlertInput = z.infer<typeof CreateAlertSchema>
export type UpdateAlertInput = z.infer<typeof UpdateAlertSchema>
