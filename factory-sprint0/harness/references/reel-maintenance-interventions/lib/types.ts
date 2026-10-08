// ── AUTO-GÉNÉRÉ PAR dev_types_generator.py — NE PAS MODIFIER ────────────────
// Source de vérité des types partagés entre tous les fichiers du projet.
// Regénéré à chaque run depuis ProjectSpec.
// ─────────────────────────────────────────────────────────────────────────────

import type { Prisma, InterventionStatus } from '@prisma/client'
export type { Prisma, InterventionStatus }
// Types Prisma — disponibles après `prisma generate`
export type { Intervention, Client, Technician, Invoice } from '@prisma/client'

// Type de réponse API standard — utilise-le dans tous les route handlers
export type ApiResponse<T> = {
  data: T | null
  error: string | null
  success: boolean
}

// Type de réponse paginée
export type PaginatedResponse<T> = ApiResponse<T[]> & {
  total: number
  page: number
  pageSize: number
}

// Types d'entrée pour Intervention
export type CreateInterventionInput = Omit<Prisma.InterventionUncheckedCreateInput, 'createdAt' | 'id' | 'updatedAt' | 'userId'>
export type UpdateInterventionInput = Partial<CreateInterventionInput>

// Intervention — retour service (DateTime → string, NE PAS appeler .toISOString())
export type SerializedIntervention = {
  id: string
  date: string
  status: InterventionStatus
  clientId: string
  client?: { id: string; name: string; email: string; phone: string | null; address: string | null; createdAt: string; updatedAt: string }
  technicianId: string | null
  technician?: { id: string; name: string; email: string; phone: string | null; region: string | null; createdAt: string; updatedAt: string }
  createdAt: string
  updatedAt: string
}

// Types d'entrée pour Client
export type CreateClientInput = Omit<Prisma.ClientUncheckedCreateInput, 'createdAt' | 'id' | 'updatedAt' | 'userId'>
export type UpdateClientInput = Partial<CreateClientInput>

// Client — retour service (DateTime → string, NE PAS appeler .toISOString())
export type SerializedClient = {
  id: string
  name: string
  email: string
  phone: string | null
  address: string | null
  interventions?: { id: string; date: string; status: InterventionStatus; clientId: string; technicianId: string | null; createdAt: string; updatedAt: string }[]
  createdAt: string
  updatedAt: string
}

// Types d'entrée pour Technician
export type CreateTechnicianInput = Omit<Prisma.TechnicianUncheckedCreateInput, 'createdAt' | 'id' | 'updatedAt' | 'userId'>
export type UpdateTechnicianInput = Partial<CreateTechnicianInput>

// Technician — retour service (DateTime → string, NE PAS appeler .toISOString())
export type SerializedTechnician = {
  id: string
  name: string
  email: string
  phone: string | null
  region: string | null
  interventions?: { id: string; date: string; status: InterventionStatus; clientId: string; technicianId: string | null; createdAt: string; updatedAt: string }[]
  createdAt: string
  updatedAt: string
}

// Types d'entrée pour Invoice
export type CreateInvoiceInput = Omit<Prisma.InvoiceUncheckedCreateInput, 'createdAt' | 'id' | 'updatedAt' | 'userId'>
export type UpdateInvoiceInput = Partial<CreateInvoiceInput>

// Invoice — retour service (DateTime → string, NE PAS appeler .toISOString())
export type SerializedInvoice = {
  id: string
  number: string
  date: string
  pdfUrl: string
  clientId: string
  client?: { id: string; name: string; email: string; phone: string | null; address: string | null; createdAt: string; updatedAt: string }
  technicianId: string | null
  technician?: { id: string; name: string; email: string; phone: string | null; region: string | null; createdAt: string; updatedAt: string }
  createdAt: string
  updatedAt: string
}

// Paramètres de route pour les pages dynamiques
export type InterventionIdPageParams = { params: Promise<{ id: string }> }
export type ClientIdPageParams = { params: Promise<{ id: string }> }
export type TechnicianIdPageParams = { params: Promise<{ id: string }> }
export type InvoiceIdPageParams = { params: Promise<{ id: string }> }

// Types Clerk — userId garanti non-null dans les routes protégées
export type AuthenticatedRequest = Request & { auth: { userId: string } }
