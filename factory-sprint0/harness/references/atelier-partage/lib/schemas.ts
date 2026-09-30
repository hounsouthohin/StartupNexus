// AUTO-GÉNÉRÉ PAR dev_zod_generator.py — NE PAS MODIFIER
// Schémas Zod alignés sur lib/types.ts et ProjectSpec.
// Utilisé dans les Server Actions pour valider les données entrantes.
import { z } from 'zod'

// ── Workshop ──────────────────────────────────────────────────
export const CreateWorkshopSchema = z.object({
  title: z.string().min(1),
  description: z.string().min(1),
  duration: z.coerce.number().int().nonnegative(),
  price: z.coerce.number().nonnegative(),
  domainIds: z.array(z.string()).optional(),
})

export const UpdateWorkshopSchema = z.object({
  title: z.string().optional(),
  description: z.string().optional(),
  duration: z.coerce.number().int().nonnegative().optional(),
  price: z.coerce.number().nonnegative().optional(),
  domainIds: z.array(z.string()).optional(),
})
export type CreateWorkshopInput = z.infer<typeof CreateWorkshopSchema>
export type UpdateWorkshopInput = z.infer<typeof UpdateWorkshopSchema>

// ── Domain ──────────────────────────────────────────────────
export const CreateDomainSchema = z.object({
  name: z.string().min(1),
  workshopIds: z.array(z.string()).optional(),
})

export const UpdateDomainSchema = z.object({
  name: z.string().optional(),
  workshopIds: z.array(z.string()).optional(),
})
export type CreateDomainInput = z.infer<typeof CreateDomainSchema>
export type UpdateDomainInput = z.infer<typeof UpdateDomainSchema>

// ── Slot ──────────────────────────────────────────────────
export const CreateSlotSchema = z.object({
  startTime: z.coerce.date(),
  endTime: z.coerce.date(),
})

export const UpdateSlotSchema = z.object({
  startTime: z.coerce.date().optional(),
  endTime: z.coerce.date().optional(),
})
export type CreateSlotInput = z.infer<typeof CreateSlotSchema>
export type UpdateSlotInput = z.infer<typeof UpdateSlotSchema>

// ── Reservation ──────────────────────────────────────────────────
export const CreateReservationSchema = z.object({
  slotId: z.string().min(1),
})

export const UpdateReservationSchema = z.object({
  status: z.enum(["pending", "confirmed", "cancelled", "completed"]).optional(),
  reason: z.string().optional(),
  slotId: z.string().optional(),
})
export type CreateReservationInput = z.infer<typeof CreateReservationSchema>
export type UpdateReservationInput = z.infer<typeof UpdateReservationSchema>
