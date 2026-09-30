// AUTO-GÉNÉRÉ PAR dev_zod_generator.py — NE PAS MODIFIER
// Schémas Zod alignés sur lib/types.ts et ProjectSpec.
// Utilisé dans les Server Actions pour valider les données entrantes.
import { z } from 'zod'

// ── Client ──────────────────────────────────────────────────
export const CreateClientSchema = z.object({
  name: z.string().min(1),
  phone: z.string().min(1),
})

export const UpdateClientSchema = z.object({
  name: z.string().optional(),
  phone: z.string().optional(),
})
export type CreateClientInput = z.infer<typeof CreateClientSchema>
export type UpdateClientInput = z.infer<typeof UpdateClientSchema>

// ── Vehicle ──────────────────────────────────────────────────
export const CreateVehicleSchema = z.object({
  brand: z.string().min(1),
  model: z.string().min(1),
  licensePlate: z.string().min(1),
  clientId: z.string().min(1),
})

export const UpdateVehicleSchema = z.object({
  brand: z.string().optional(),
  model: z.string().optional(),
  licensePlate: z.string().optional(),
  clientId: z.string().optional(),
})
export type CreateVehicleInput = z.infer<typeof CreateVehicleSchema>
export type UpdateVehicleInput = z.infer<typeof UpdateVehicleSchema>

// ── Repair ──────────────────────────────────────────────────
export const CreateRepairSchema = z.object({
  description: z.string().min(1),
  vehicleId: z.string().min(1),
})

export const UpdateRepairSchema = z.object({
  description: z.string().optional(),
  status: z.enum(["pending", "accepted", "rejected", "in_progress", "completed"]).optional(),
  reasonForRejection: z.string().optional(),
  amountCharged: z.coerce.number().nonnegative().optional(),
  vehicleId: z.string().optional(),
})
export type CreateRepairInput = z.infer<typeof CreateRepairSchema>
export type UpdateRepairInput = z.infer<typeof UpdateRepairSchema>
