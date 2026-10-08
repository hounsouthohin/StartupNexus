// AUTO-GÉNÉRÉ PAR dev_zod_generator.py — NE PAS MODIFIER
// Schémas Zod alignés sur lib/types.ts et ProjectSpec.
// Utilisé dans les Server Actions pour valider les données entrantes.
import { z } from 'zod'

// ── Client ──────────────────────────────────────────────────
export const CreateClientSchema = z.object({
  name: z.string().min(1),
  email: z.string().email(),
  address: z.string().min(1),
})

export const UpdateClientSchema = z.object({
  name: z.string().optional(),
  email: z.string().email().optional(),
  address: z.string().optional(),
})
export type CreateClientInput = z.infer<typeof CreateClientSchema>
export type UpdateClientInput = z.infer<typeof UpdateClientSchema>

// ── Machine ──────────────────────────────────────────────────
export const CreateMachineSchema = z.object({
  model: z.string().min(1),
  serialNumber: z.string().min(1),
  socket: z.enum(["478", "754", "775", "am2"]),
  clientId: z.string().min(1),
})

export const UpdateMachineSchema = z.object({
  model: z.string().optional(),
  serialNumber: z.string().optional(),
  socket: z.enum(["478", "754", "775", "am2"]).optional(),
  clientId: z.string().optional(),
})
export type CreateMachineInput = z.infer<typeof CreateMachineSchema>
export type UpdateMachineInput = z.infer<typeof UpdateMachineSchema>

// ── Intervention ──────────────────────────────────────────────────
export const CreateInterventionSchema = z.object({
  date: z.coerce.date(),
  machineId: z.string().min(1),
})

export const UpdateInterventionSchema = z.object({
  date: z.coerce.date().optional(),
  status: z.enum(["ouverte", "en_cours", "cloturee", "payee"]).optional(),
  machineId: z.string().optional(),
})
export type CreateInterventionInput = z.infer<typeof CreateInterventionSchema>
export type UpdateInterventionInput = z.infer<typeof UpdateInterventionSchema>

// ── Action ──────────────────────────────────────────────────
export const CreateActionSchema = z.object({
  description: z.string().min(1),
  interventionId: z.string().min(1),
})

export const UpdateActionSchema = z.object({
  description: z.string().optional(),
  status: z.enum(["a_faire", "faite"]).optional(),
  interventionId: z.string().optional(),
})
export type CreateActionInput = z.infer<typeof CreateActionSchema>
export type UpdateActionInput = z.infer<typeof UpdateActionSchema>
