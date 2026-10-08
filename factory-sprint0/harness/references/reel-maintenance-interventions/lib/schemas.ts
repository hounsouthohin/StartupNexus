// AUTO-GÉNÉRÉ PAR dev_zod_generator.py — NE PAS MODIFIER
// Schémas Zod alignés sur lib/types.ts et ProjectSpec.
// Utilisé dans les Server Actions pour valider les données entrantes.
import { z } from 'zod'

// ── Intervention ──────────────────────────────────────────────────
export const CreateInterventionSchema = z.object({
  date: z.coerce.date(),
  clientId: z.string().min(1),
  technicianId: z.string().min(1),
})

export const UpdateInterventionSchema = z.object({
  date: z.coerce.date().optional(),
  status: z.enum(["planned", "confirmed", "completed", "cancelled"]).optional(),
  clientId: z.string().optional(),
  technicianId: z.string().optional(),
})
export type CreateInterventionInput = z.infer<typeof CreateInterventionSchema>
export type UpdateInterventionInput = z.infer<typeof UpdateInterventionSchema>

// ── Client ──────────────────────────────────────────────────
export const CreateClientSchema = z.object({
  name: z.string().min(1),
  email: z.string().email(),
  phone: z.string().optional(),
  address: z.string().optional(),
})

export const UpdateClientSchema = z.object({
  name: z.string().optional(),
  email: z.string().email().optional(),
  phone: z.string().optional(),
  address: z.string().optional(),
})
export type CreateClientInput = z.infer<typeof CreateClientSchema>
export type UpdateClientInput = z.infer<typeof UpdateClientSchema>

// ── Technician ──────────────────────────────────────────────────
export const CreateTechnicianSchema = z.object({
  name: z.string().min(1),
  email: z.string().email(),
  phone: z.string().optional(),
  region: z.string().optional(),
})

export const UpdateTechnicianSchema = z.object({
  name: z.string().optional(),
  email: z.string().email().optional(),
  phone: z.string().optional(),
  region: z.string().optional(),
})
export type CreateTechnicianInput = z.infer<typeof CreateTechnicianSchema>
export type UpdateTechnicianInput = z.infer<typeof UpdateTechnicianSchema>

// ── Invoice ──────────────────────────────────────────────────
export const CreateInvoiceSchema = z.object({
  number: z.string().min(1),
  date: z.coerce.date(),
  pdfUrl: z.string().url(),
  clientId: z.string().min(1),
  technicianId: z.string().min(1),
})

export const UpdateInvoiceSchema = z.object({
  number: z.string().optional(),
  date: z.coerce.date().optional(),
  pdfUrl: z.string().url().optional(),
  clientId: z.string().optional(),
  technicianId: z.string().optional(),
})
export type CreateInvoiceInput = z.infer<typeof CreateInvoiceSchema>
export type UpdateInvoiceInput = z.infer<typeof UpdateInvoiceSchema>
